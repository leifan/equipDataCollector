# encoding:utf-8
import time
import datetime
import os
import sys, configparser
import logging
from logging.handlers import RotatingFileHandler
from threading import Thread, Event
from queue import Queue, Empty
from collections import deque, defaultdict
from itertools import groupby

from proto import MetaRegCls
from get_gate_way_info import GetGateWayInfo, udp_gw

import socket
import json
import struct
import requests

# 采集线程N
# 需要处理接口协议，多客户端轮询，单客户查询
class Collector(Thread):
    def __init__(self, qData, qSetData, ch, addrs, period, space=0.05):
        super().__init__(daemon=True)
        self.finished = Event()
        self.qData = qData
        self.qSetData = qSetData
        self.ch = ch
        self.addrs = addrs
        self.interval = period
        self.space = space

    def stop(self):
        self.finished.set()

    def run(self):
        logging.info('通道 %s 启动:\n\t %s'%(self.ch.portName(),
                "\n\t".join(str(e) for e in self.addrs)))
        while not self.finished.is_set():
            t0 = time.time()
            # 设置
            while not self.qSetData.empty():
                time.sleep(self.space)
                setDat = self.qSetData.get() # {'status2': 0, 'equipId': 3, 'equipType': 2, 'status1': 0}
                # 判断 设置寄存器 拼接modbus命令
                # 写单线圈 5 status1 寄存器地址 0， status2 寄存器地址 1
                status = []
                if 'status1' in setDat.keys():
                    status1 = 0 if setDat['status1'] == 0 else 0xFF
                    status.append(status1)

                if 'status2' in setDat.keys():
                    status2 = 0 if setDat['status2'] == 0 else 0xFF
                    status.append(status2)
                
                if len(status):
                    for equipType,equipId,*a in self.addrs:
                        if setDat['equipType'] == 2 and setDat['equipId'] == equipId:
                            # equipType, equipId, comaddr, 功能代码,开始地址, 写入值
                            regStartAddr = 0 if 'status1' in setDat.keys() else 1 
                            ret = self.ch.setSlaveData(equipType, equipId, a[0], 15, regStartAddr, status)
                            logging.info('设置(equipType={},equipId={},addr={},value={})结果:{}'.format(equipType, equipId, a[0], status, ret))

            # 采集
            for equipType,equipId,*a in self.addrs: # equipType, equipId, comaddr, 功能代码, 开始地址, 读寄存器个数
                time.sleep(self.space)
                ret = self.ch.getSlaveData(equipType,equipId,*a)
                if ret['comStatus']:
                    logging.debug('采集(equipType={},equipId={})解析数据:{}'.format(equipType, equipId, ret))  
                else:
                    logging.warning('{} {} {}'.format(self.ch.portName(), '通信故障', a))
                
                '''
                有毒气体qData一体记录数据
                通讯正常数据 {dataType='ToxicGas','equipType'=3, 'equipId'=5, 'modbusaddr'=1 ,'comStatus'=1,'concentration'= 0.0}
                通讯故障数据 {dataType='ToxicGas','equipType'=3, 'equipId'=6, 'modbusaddr'=2 ,'comStatus'=0}
                '''
                self.qData.put(ret)

            left = self.interval - (time.time() - t0)
            if left > 0.1:
                time.sleep(left)
            logging.debug('%s轮询用去%.3f秒'%(self.ch.portName(), self.interval-left))

        self.ch.close()
        logging.info('通道 %s 关闭'%self.ch.portName())

# 设备数据主动上报 线程
class Writer(Thread):
    def __init__(self, qData, web_cfg_info):
        super().__init__(daemon=True)
        self.finished = Event()
        self.qData = qData
        self.web_cfg_info = web_cfg_info
        self.interval = 2.0
        self.concentration = 0
        self.runSecondTime = 0
        self.equipList = [] # web获取设备列表
        self.caches = {} # 缓存设备数据

    def stop(self):
        self.finished.set()
    
    def GetSessionId(self):
        '''
        登录获取sessionId
        web返回格式
        {
            "code": 200,
            "data": {
                "createTime": "2020-05-16 16:02:48",
                "creator": "商云辉",
                "realName": "采集器账号",
                "sessionId": "b53fed801bc3d869de6eeab52de2c628",
                "tel": "18729019999",
                "userId": 22,
                "userName": "youduqiti@00001"
            },
            "desc": "成功"
        }
        '''
        try:
            url = self.web_cfg_info['web_login_url']
            params = {'userName': self.web_cfg_info['userName'], 
                      'password': self.web_cfg_info['password'],
                    }
            r = requests.get(url=url, params=params)
            d = r.json()
            sessionId = d['data']['sessionId']
            self.web_cfg_info['sessionId'] = sessionId
            logging.info('获取sessionId={}'.format(sessionId))
        except Exception as e:
            logging.warning(str(e), exc_info=True)

        return None

    def GetToxicGasEquipData(self, dat):
        '''
        获取设备数据
        1、采集的有毒气体设备数据
        2、web设备列表匹配待发送数据
        '''
        if not dat or 'ToxicGas' != dat['dataType'] : # 筛选取有毒气体相关数据
            return None
        try:
            # qData {'equipType'=3, 'equipId'=5, 'modbusaddr'=1 ,'comStatus'=1,'concentration'= 0.0}
            equip_info = '{}_{}_{}'.format(dat.get('equipType'), dat.get('equipId'), dat.get('modbusaddr'))
            # 匹配web获取的设备列表
            for s in self.equipList: 
                if dat['equipType'] == s['equipType'] and dat['equipId'] == s['id']:
                    d = {
                        "equipType": s['equipType'],
                        "equipCode": s['equipCode'],
                        "appId"    : self.web_cfg_info['appId'],
                        "id"       : s['id'],
                        "comStatus": dat['comStatus'],
                        }

                    if 'concentration' in dat :
                        d.update({"value": dat['concentration']})
                    
                    cdat = self.caches.setdefault(equip_info, {})
                    # cache is a dict of key('4_5_1') with ( d ) elements
                    # self.caches 缓存设备数据 上报条件5分钟或者数据变化
                    if cdat != d or self.runSecondTime % int(self.web_cfg_info['report_interval']) == 0 : 
                        self.caches.update({equip_info : d})
                        return {equip_info : d}
        except Exception as e:
            logging.warning(str(e), exc_info=True)
        return None

    def GetLvMiEquipData(self, dat):
        '''
        获取绿米相关设备数据
        '''
        if not dat or 'LvMi' != dat['dataType']: # 筛选绿米设备相关数据
            return None

        equipDat = {}
        # dataType='LvMi', sid=sid, comStatus=1, params=heart_dat.get('params')

        # 设备相关数据提取
        # 举例温湿度参数 'params': [{'battery_voltage': 2985}, {'temperature': 2356}, {'humidity': 6183}, {'pressure': 95443}]
        # 温湿度传感器的数据需要拆开 分为 
        # equipType = 1 湿度
        # equipType = 2 温度 
        # equipType = 3 压力 
        for k in dat['params']:
            equipType = 1
            value = 0
            if 'temperature' in k:
                equipType = 1
                value = k['temperature']
            elif 'humidity' in k:
                equipType = 2
                value = k['humidity']
            elif 'pressure' in k:   
                equipType = 3
                value = k['pressure']
            else :
                continue
            
            sid = dat.get('sid') 
            for s in self.equipList:
                deviceId = s['deviceId']
                eType = s['equipType']
                if sid and deviceId and sid in deviceId and equipType == eType:
                    d = {"equipType": s['equipType'],
                        "equipCode": s['equipCode'],
                        "appId"    : self.web_cfg_info['appId'],
                        "id"       : s['id'],
                        "comStatus": dat['comStatus'],
                        "value"    : value,
                        }
                    equipDat.update({sid : d})
        return equipDat
     
    def SendEquipDatatoWeb(self, equipDat):
        '''
        上报有毒气体数据
        上传格式举例： data = [{"equipType":4,:equipCode":"005","appId":"00001","value":10}]
        web返回格式
        {
            "code": 200,
            "desc": "成功"
        }
        '''
        if not equipDat:
           return None

        if  not self.web_cfg_info.get('sessionId'):
            return None

        try:
            url = self.web_cfg_info['web_post_toxic_url']
            headers = {
                        'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
                        'Cookie':'sessionId={}'.format(self.web_cfg_info['sessionId']),
                    }
            params = {'data': json.dumps(equipDat)}
            r = requests.post(url=url, headers=headers, params=params)
            logging.info('上报数据 {} 结果:{} {}'.format(params, r, r.content.decode('utf-8')))
        except Exception as e:
            logging.warning(str(e), exc_info=True)
        return None

    def GetEquipInfoFromWeb(self):
        '''
        获取设备列表 
        web返回格式
        {
            "code": 200,
            "data": {
                "list": [
                    {
                        "createTime": 1590951785000,
                        "createTimePlain": "2020-06-01 03:03:05",
                        "creator": "王",
                        "deviceId": "",
                        "effect": "",
                        "equipBrand": "其他",
                        "equipCode": "005",
                        "equipName": "有毒气体臭氧",
                        "equipStatus": 0,
                        "equipType": 4,
                        "frequency": 10,
                        "id": 5,
                        "joinType": 2,
                        "showId": 1,
                        "threshold": 1.00
                    },
                ],
                "pagination": {
                    "currentPage": 1,
                    "limit": 25,
                    "offset": 0,
                    "recordPerPage": 25,
                    "totalPage": 1,
                    "totalRecord": 1
                }
            },
            "desc": "成功"
        }
        '''
        equipList = []
        try:
            url = self.web_cfg_info['web_get_toxic_equip_url']
            headers = {
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'Cookie'      : 'sessionId={}'.format(self.web_cfg_info['sessionId']),
                      }
            params= { 'sessiondId'   : self.web_cfg_info['sessionId'], 
                      'recordPerPage': self.web_cfg_info['recordPerPage'] 
                    }
            r = requests.post(url=url, headers=headers, params=params)
            r2 = r.json()
            equipList = r2['data']['list'] or []
            print(equipList)
            logging.info('获取设备{}个 结果:{} {}'.format(len(equipList), r, r.content.decode('utf-8')))
        except Exception as e:
            logging.warning(str(e), exc_info=True)

        # 更新有毒气体设备列表
        self.equipList = [x for x in equipList]
        return self.equipList

    def run(self):
        '''
        任务1：每10分钟获取sessionId
        任务2：每5分钟获取有毒气体设备列表
        任务3：每5分钟上报有毒气体数据 上报条件5分钟或者数据变化
        '''
        while not self.finished.is_set():
            try:
                time.sleep(1)

                if self.runSecondTime % 600 == 0: #10分钟
                    self.GetSessionId()
                    time.sleep(1)

                if self.runSecondTime % 300 == 0: # 300 = 5分钟 180=3分钟
                    self.GetEquipInfoFromWeb()
                    time.sleep(1)

                if self.runSecondTime % 3 == 0: # 3s
                    equipDat = {}
                    while not self.qData.empty(): 
                        dat = self.qData.get()
                        equipDat.update(self.GetToxicGasEquipData(dat) or {}) # 获取有毒气体数据
                        equipDat.update(self.GetLvMiEquipData(dat) or {}) # 获取绿米设备数据

                    if len(equipDat):
                        self.SendEquipDatatoWeb(list(equipDat.values())) # 发送数据
                    time.sleep(1)
            
                self.runSecondTime += 1
            except Exception as e:
                logging.warning(str(e), exc_info=True)
        
        logging.info('Writer 结束')

# 获取空调伴侣网关 线程
class Recevie(Thread):
    def __init__(self, qData, web_cfg_info):
        super().__init__(daemon=True)
        self.finished = Event()
        self.qData = qData
        self.interval = 2.0
        self.runSecondTime = 0

    def stop(self):
        self.finished.set()

    def run(self):
        logging.info('开始获取网关信息')
        gw_all = GetGateWayInfo()
        gateWay_list = gw_all.GetGateWayEquipInfo()
        logging.info('获取网关信息：{}'.format(gateWay_list))

        # 获取网关ip,创建网关
        gw_list = []
        for a in gateWay_list:
            gw_list.append(udp_gw(a['ip']))
        
        # 获取每个网关下子设备 获取sid
        '''
        {
        'gateway_50ec50c708fa': '50ec50c708fa', 
        'plug_158d000392613e': '158d000392613e', 
        'remote.b186acn01_158d0004563c17': '158d0004563c17', 
        'weather_158d00045c946f': '158d00045c946f'
        }
        '''
        sid_list = [] # 所有子设备sid
        for gw in gw_list:
            time.sleep(5)
            d = gw.get_dict_model_sid()
            sid_list += d.values()
            print('get_dict_model_sid=', d, 'sid_list=', sid_list)

        
        HEART_CHECK_TIME = 60 * 60 # 温湿度心跳检测时间(秒)
        weather_sid_dat = {} # 记录温湿度数据
        
        # 轮询子设备心跳包    
        while not self.finished.is_set():
            # {"cmd":"heartbeat","model":"acpartner.v3","sid":"50ec50c708fa","token":"VdcDlmz9KOALtG3F","params":[{"ip":"192.168.1.102"}]}
            # {"cmd":"report","model":"weather","sid":"158d00045c946f","params":[{"temperature":2526}]}
            starttime = datetime.datetime.now() # 当前时间
            heart_dat = gw_all.GetGatewayHeart()
            sid =  heart_dat.get('sid')
            model = heart_dat.get('model')
            if sid and 'acpartner' not in model:
                d = dict(dataType='LvMi', sid=sid, comStatus=1, params=heart_dat.get('params')) 
                print('*'*50)
                print(d)
                print('***绿米设备***'*5)
                self.qData.put(d) 

            if sid in weather_sid_dat:
                weather_sid_dat[sid] = HEART_CHECK_TIME
            
            endtime = datetime.datetime.now()
            runtime = (endtime - starttime).seconds

            for sid in weather_sid_dat:
                weather_sid_dat[sid] = weather_sid_dat[sid] - runtime
                if weather_sid_dat[sid] <= 0 :
                    d = dict(dataType='LvMi', sid=sid, comStatus=0, params=None) 
                    self.qData.put(d) 

        logging.info('Recevie 结束')


# 解析配置文件
class EquipCfg:
    def __init__(self, fname):
        self.fullname = os.path.join(os.getcwd(), fname)
        conf = configparser.SafeConfigParser()
        try:
            with open(self.fullname, 'r', encoding="utf-8") as fp:
                conf.read_file(fp)
        except:
            pass
        self.parser = conf

    def get_option(self, section, name):
        ret = None
        try:
            ret = self.parser.get(section, name)
        except:
            pass
        return ret

    def get_all_info(self):

        return self.get_channel(), self.get_web_cfg()

    def get_channel(self):
        channels = []
        try:
            num = self.get_option('channel_cfg', 'channel_max_num')
            for i in range(1, int(num) + 1):
                ch = self.get_option('channel_cfg', 'channel_' + str(i)) # channel_1 = COM1,rtu_modbus,2500,None,100,200
                if ch:
                    t = ch.split(',')
                    t[2], t[4], t[5] = int(t[2]), int(t[4]), int(t[5]),
                    t[3] = self.get_equipinfo(i)
                    channels.append(t)
        except Exception as e:
            logging.warning(str(e), exc_info=True)
        return channels
    
    def get_equipinfo(self,channelIndex):
        equipinfo = []
        try:
            num = self.get_option('equip_cfg', 'equip_num')
            for i in range(1, int(num) + 1):
                ch = self.get_option('equip_cfg', 'equip_' + str(i)) # 1,1,1,1,3,0,2
                if ch:
                    t = ch.split(',')
                    if int(t[0]) == channelIndex: # 判断通道
                        t.pop(0)
                        ti = [int(x) for x in t]
                        equipinfo.append(ti)
        except Exception as e:
            logging.warning(str(e), exc_info=True)
        return equipinfo
    
    def get_web_cfg(self):
        web_cfg_info = {'appId':None,
                        'web_login_url':None,
                        'userName':None,
                        'password':None,
                        'web_get_toxic_equip_url':None,
                        'recordPerPage':None,
                        'web_post_toxic_url':None,
                        'report_interval':None,
                       }
        try:
            for k in web_cfg_info.keys():
                ret = self.get_option('web_cfg', k) 
                if ret:
                    web_cfg_info[k] = ret
            print(web_cfg_info)
        except Exception as e:
            logging.warning(str(e), exc_info=True)
        return web_cfg_info       

# 获取设备基本信息
def getBasic(engine, Base):
    try:
        cfg = EquipCfg('equipCfg.ini')
        web_cfg_info, channel_cfg_info = cfg.get_all_info()
        return web_cfg_info, channel_cfg_info
    except Exception as e:
        logging.warning(str(e), exc_info=False)

    return [], None

class HtDac():
    def __init__(self, info):
        self.engine = info # (host, port, com, timeout)
        self.hBase = None
        self.threads = []
        self.qData = None
        self.qSetData = None
        self.msg_err = []

    def startDac(self):

        print(self.engine) # 打印窗体设置参数

        # 获取配置信息
        channel_cfg_info, web_cfg_info = getBasic(self.engine, self.hBase)

        if not channel_cfg_info or self.threads: #不可重复执行
            return [], None, None

        qData = Queue(maxsize=0)     # 设备采集数据
        qSetData = Queue(maxsize=0)  # 设备设置数据
        threads = []  # 存所有线程               

        # 设备采集所有线程
        for p in channel_cfg_info: 
            chCls = MetaRegCls.getClass(p[1])
            if chCls and p[3]:
                ch = chCls(p[0], p[4]/1000.) # 串口， 超时时间
                if ch.master:
                    cltor = Collector(qData, qSetData, ch, p[3], p[2]/1000., p[5]/1000.) # Collector(采集数据, 通道, 地址信息， 间隔时间，延迟时间)   
                    threads.append(cltor)
                else:
                    self.msg_err.append(ch.msg_err)
       
        # web所有线程
        if web_cfg_info:
            writer = Writer(qData, web_cfg_info)
            threads.append(writer)

            recevie = Recevie(qData, web_cfg_info) # 获取绿米网关相关信息
            threads.append(recevie)

        # 启动所有线程
        for t in threads:
            t.start()

        self.threads = threads
        self.qData = qData
        self.qSetData = qSetData

        return threads, qData, qSetData

    def endDac(self):
        for t in self.threads: t.stop()
        for t in self.threads: t.join(t.interval)
        self.threads = []

    def monitor(self):
        '''
        实现配置变化时动态修改参数
        '''
        if not all(t.is_alive() for t in self.threads):
            logging.warn('存在死亡线程')
        
        if len(self.msg_err):
            logging.warn('{}'.format(self.msg_err))

        return True
