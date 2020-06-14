# encoding:utf-8
import time
from datetime import datetime, timezone
import os
import sys, configparser
import logging
from logging.handlers import RotatingFileHandler
from threading import Thread, Event
from queue import Queue, Empty
from collections import deque, defaultdict
from itertools import groupby

from proto import MetaRegCls

import socket
import json
import struct
import requests

COM_STATUS_NORMAL   = 1 # 通讯正常
COM_STATUS_ABNORMAL = 0 # 通讯异常


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
                comStatus = COM_STATUS_NORMAL
                if ret:
                    logging.debug('采集(equipType={},equipId={})解析数据:{}'.format(equipType, equipId, ret))  
                else:
                    comStatus = COM_STATUS_ABNORMAL
                    logging.warning('{} {} {}'.format(self.ch.portName(), '通信故障', a))
                
                '''
                有毒气体qData一体记录数据
                {'equipType'=3, 'equipId'=5, 'modbusaddr'=1 ,'comStatus'=1,'concentration'= 0.0}
                {'equipType'=3, 'equipId'=6, 'modbusaddr'=2 ,'comStatus'=1,'concentration'= 1.0}
                '''
                ret.update(equipType=equipType, equipId=equipId, modbusaddr=a[0], comStatus=comStatus)
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
        self.toxiGasEquipList = [] # web获取设备列表
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

    def GetEquipData(self):
        '''
        获取设备数据
        1、采集的有毒气体设备数据
        2、web设备列表匹配待发送数据
        '''
        try:
            dat = {}
            equipDatList = {}
            # qData {'equipType'=3, 'equipId'=5, 'modbusaddr'=1 ,'comStatus'=1,'concentration'= 0.0}
            while not self.qData.empty(): 
                dat = self.qData.get()
                equip_info = '{}_{}_{}'.format(dat.get('equipType'), dat.get('equipId'), dat.get('modbusaddr'))
                equipDatList.update({equip_info:dat})

            print('获取设备数据个数：', len(equipDatList), 'equipDatList:', equipDatList)

            # 匹配web获取的设备列表
            equipDat = []
            for k, info in equipDatList.items(): # {'4_5_1': {'equipType'=3, 'equipId'=5, 'modbusaddr'=1 ,'comStatus'=1,'concentration'= 0.0}, }
                for s in self.toxiGasEquipList: # 
                    if info['equipType'] == s['equipType'] and info['equipId'] == s['id']:
                        d = {"equipCode": s['equipCode'],
                            "appId"    : self.web_cfg_info['appId'],
                            "id"       : s['id'],
                            "comStatus": info['comStatus'],
                            }

                        if 'concentration' in info :
                            d.update({"concentration": info['concentration']})
                        
                        cdat = self.caches.setdefault(k, {})
                        # cache is a dict of key('4_5_1') with ( d ) elements
                        # self.caches 缓存设备数据 上报条件5分钟或者数据变化
                        if cdat != d or self.runSecondTime % 300 == 0 : 
                            self.caches.update({k:d})
                            equipDat.append(d)
            
            print('待发送设备数据个数：', len(equipDat),'equipDat=', equipDat)
            return equipDat
        except Exception as e:
            logging.warning(str(e), exc_info=True)
        return None

    def SendEquipDatatoWeb(self):
        '''
        上报有毒气体数据
        上传格式： data = [{"equipCode":"005","appId":"00001","value":10}]
        web返回格式
        {
            "code": 200,
            "desc": "成功"
        }
        '''
        if self.qData.empty() or 'sessionId' not in self.web_cfg_info.keys():
            return None

        equipDat = self.GetEquipData()
       
        if not equipDat:
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
        self.toxiGasEquipList = [x for x in equipList]
        return self.toxiGasEquipList

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

                if self.runSecondTime % 300 == 0: #5分钟
                    self.GetEquipInfoFromWeb()
                    time.sleep(1)

                if self.runSecondTime % 3 == 0: # 3s
                    self.SendEquipDatatoWeb()
                    time.sleep(1)
            
                self.runSecondTime += 1
            except Exception as e:
                logging.warning(str(e), exc_info=True)
        
        logging.info('Writer 结束')

# 获取服务器数据 线程
class Recevie(Thread):
    def __init__(self, qData):
        super().__init__(daemon=True)
        self.finished = Event()
        self.qData = qData
        self.interval = 2.0

    def stop(self):
        self.finished.set()

    def run(self):
        while not self.finished.is_set():
            pass

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

            # recevie = Recevie(qSetData, self.handle_socket)
            # threads.append(recevie)

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
