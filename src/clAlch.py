# encoding:utf-8
import time
from datetime import datetime, timezone
import os, sqlite3

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

HANDLE_SOCKET = None

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
                status1 = 0 if setDat['status1'] == 0 else 0xFF
                status2 = 0 if setDat['status2'] == 0 else 0xFF
                status = [status1,status2]
                print(status)
                for equipType,equipId,*a in self.addrs:
                    if setDat['equipType'] == 2 and setDat['equipId'] == equipId:
                        ret = self.ch.setSlaveData(equipType, equipId, a[0], 15, 0, status)# equipType, equipId, comaddr, 功能代码,开始地址, 写入值

            # 采集
            for equipType,equipId,*a in self.addrs: # equipType, equipId, comaddr, 功能代码,开始地址,读寄存器个数
                time.sleep(self.space)
                ret = self.ch.getSlaveData(equipType,equipId,*a)
                comStatus = 1
                if ret:
                    #current = datetime.now(tz=timezone.utc)
                    #print(ret)
                    self.qData.put(ret)
                else:
                    comStatus = 0
                    logging.warning('{} {} {}'.format(self.ch.portName(), '通信故障', a))
                ret.update(equipType=equipType, equipId=equipId, modbusaddr=a[0], comStatus=comStatus)

            left = self.interval - (time.time() - t0)
            if left > 0.1:
                time.sleep(left)
            logging.debug('%s轮询用去%.3f秒'%(self.ch.portName(), self.interval-left))

        self.ch.close()
        logging.info('通道 %s 关闭'%self.ch.portName())

# 设备数据主动上报 线程
class Writer(Thread):
    def __init__(self, qData, handle_socket):
        super().__init__(daemon=True)
        self.finished = Event()
        self.qData = qData
        self.interval = 2.0
        self.handle_socket = handle_socket

    def stop(self):
        self.finished.set()

    def run(self):
        while not self.finished.is_set():
            # 主动上报数据
            if not self.qData.empty() or self.handle_socket:
                json_str = json.dumps(self.qData.get())
                json_d = json_str.encode('utf-8')
                dat = struct.pack('<H', 0xAAFF) + len(json_d).to_bytes(4, byteorder='big') + json_d
                self.handle_socket.sendall(dat)      #数据上报服务器
                logging.info('主动上报 {}'.format(dat))
            time.sleep(3)
        logging.info('Writer 结束')

# 获取服务器数据 线程
class Recevie(Thread):
    def __init__(self, qData, handle_socket):
        super().__init__(daemon=True)
        self.finished = Event()
        self.qData = qData
        self.interval = 2.0
        self.handle_socket = handle_socket

    def stop(self):
        self.finished.set()

    def run(self):
        msgFlag = 0
        msgLen = 0
        while not self.finished.is_set():
            if self.handle_socket:
                if msgFlag == 0: # 帧头校验
                    d = self.handle_socket.recv(2) 
                    if len(d) == 2 :
                        if not (d[0] == 0xFF and d[1] == 0xAA):
                            logging.warning('帧头错误 {} {}'.format(d[0], d[1]))
                        else:
                            msgFlag = 1
                elif msgFlag == 1: # 数据长度
                    d = self.handle_socket.recv(4) 
                    if len(d) == 4:
                        msgLen = struct.unpack('>i',d)[0]
                        msgFlag = 2
                    else:
                        msgFlag = msgLen = 0
                elif msgFlag == 2: # json体
                    d = self.handle_socket.recv(msgLen) 
                    json_str = d.decode('utf-8')
                    dict_dat = json.loads(json_str)
                    self.qData.put(dict_dat)
                    print('接收->',dict_dat)
                    msgFlag = msgLen = 0

        logging.info('Recevie 结束')

# 获取设备基本信息
def getBasic(engine, Base):
    try:
        # 通道
        channels =[]
        # 测试赋值
        comStr = engine[2]
        equipSampCfg = [ # equipType, equipId, comaddr, 功能代码,开始地址,读寄存器个数)
                         # 采集
                           (0x1, 1, 1, 3, 0, 2), 
                        #  (0x1, 2, 2, 3, 0, 2), 
                           (0x2, 3, 0x10, 1, 0, 8), # 读开关状态
                        #  (0x2, 4, 0x11, 1, 0, 8), 
                       ]
        channels = [  # ( 串口， 协议类型， 查询周期， [(equipType,equipId,comaddr,0), ], 超时时间，延迟)
                        (comStr, 'rtu_modbus', 2500, equipSampCfg, 1000, 200),
                   ] 

        # TCP 通信创建
        try:
            global HANDLE_SOCKET
            HANDLE_SOCKET = socket.socket(socket.AF_INET,socket.SOCK_STREAM)     # 定义socket类型，网络通信，TCP
            HANDLE_SOCKET.connect((engine[0], int(engine[1])))         # 建立ip port 连接
            #HANDLE_SOCKET.settimeout(5)
            logging.info('{}:{}创建TCP连接成功！'.format(engine[0], int(engine[1])))
        except Exception as e:
            logging.debug(str(e), exc_info=True)

        return channels, HANDLE_SOCKET
    except Exception as e:
        logging.warning(str(e), exc_info=False)

    return [], None

class HtDac():
    def __init__(self, info):
        self.engine = info # (host, port, com, timeout)
        self.hBase = None
        self.handle_socket = None
        self.threads = []
        self.qData = None
        self.qSetData = None

    def startDac(self):
        print(self.engine)
        channels, self.handle_socket = getBasic(self.engine, self.hBase)

        if not channels or self.threads: #不可重复执行
            return [], None, None

        qData = Queue(maxsize=0)     # 设备采集数据
        qSetData = Queue(maxsize=0)  # 设备设置数据

        threads = []
        for p in channels: 
            chCls = MetaRegCls.getClass(p[1])
            if chCls and p[3]:
                ch = chCls(p[0], p[4]/1000.) # 串口， 超时时间
                if ch.master:
                    cltor = Collector(qData, qSetData, ch, p[3], p[2]/1000., p[5]/1000.) # Collector(采集数据, 通道, 地址信息， 间隔时间，延迟时间)   
                    threads.append(cltor)

        for t in threads:
            t.start()

        #if threads:
        if True:
            writer = Writer(qData, self.handle_socket)
            threads.append(writer)
            writer.start()
            
            recevie = Recevie(qSetData, self.handle_socket)
            threads.append(recevie)
            recevie.start()

        self.threads = threads
        self.qData = qData
        self.qSetData = qSetData

        return threads, qData

    def endDac(self):
        for t in self.threads: t.stop()
        for t in self.threads: t.join(t.interval)
        self.handle_socket.close() #关闭连接
        self.threads = []


    def monitor(self):
        '''
        实现配置变化时动态修改参数
        '''
        return True
