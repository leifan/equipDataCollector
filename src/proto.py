import struct
import serial
import modbus_tk.modbus_rtu as tkRtu
import logging
import time

'''
exec(slave=1, function_code=READ_HOLDING_REGISTERS, starting_address=0, quantity_of_x=0, output_value=0, data_format="", expected_length=-1)
参数说明：
@slave=1 : identifier of the slave. from 1 to 247. 
@function_code=READ_HOLDING_REGISTERS：功能码
@starting_address=100：寄存器的开始地址
@quantity_of_x=3：寄存器/线圈的数量
@output_value：一个整数或可迭代的值：1/[1,1,1,0,0,1]/xrange(12)
@data_format：对接收的数据进行格式化
@expected_length：（没对这个设置过）
'''

#协议处理接口类：metaclass, protoType, master, getSlaveData, setSlaveData
class MetaRegCls(type):
    protoClsReg = {}
    def __new__(cls, name, bases, attrs):
        newcls = super().__new__(cls, name, bases, attrs)
        pro = getattr(newcls, 'protoType', None)
        if pro:
            MetaRegCls.protoClsReg[pro] = newcls
        return newcls

    @staticmethod
    def getClass(proto):
        return MetaRegCls.protoClsReg.get(proto, None)

# rtu-modbus
class modbusRtuChannel(metaclass=MetaRegCls):
    def __init__(self, portName, rtutimeout):
        try:
            se = serial.Serial(port=portName, baudrate=self.baudrate, parity=self.parity, timeout=rtutimeout)
            logging.disable(logging.ERROR) # temporarily
            self.master = tkRtu.RtuMaster(se)
            logging.disable(logging.NOTSET)
            self.master.set_timeout(rtutimeout)
        except Exception as e:
            self.master = None
            logging.warning('%s Open failed, %s'%(portName, e))

    def getSlaveData(self, equipType, equipID, slaveId, cmd, addr, num):
        return None

    def setSlaveData(self, equipType, equipID, slaveId, cmd, addr, value):
        return None

    def portName(self):
        return self.master._serial.name if self.master else ""

    def close(self):
        if self.master:
            self.master.close()

class ModbusRtuCh(modbusRtuChannel):
    protoType = 'rtu_modbus'
    baudrate, parity = 9600, 'N'

    def getSlaveData(self, equipType, equipID, slaveId, cmd, addr, num):
        try:
            r = None
            rd = {}
            if equipType == 1: #温湿度
                # execute(slave,功能代码,开始地址,quantity_of_x=0,output_value=0,data_format="",指定长度=-1)
                r = self.master.execute(slaveId, cmd, addr, num, data_format=">2h")
                # 40001 湿度 humidity 转换系数 0.1  
                # 40002 温度 temperature 转换系数 0.1 
                rd = dict(modbusaddr=slaveId, humidity = r[0]/10., temperature = r[1]/10.)  
            elif equipType == 2: # 远程继电器
                r = self.master.execute(slaveId, cmd, addr, num)
                # 获取所有开关状态 10 01 00 00 00 08 3E 8d 响应 10 01 01 03 14 B5 
                # switchStatus1 switchStatus2
                # r = (1, 1, 0, 0, 0, 0, 0, 0)
                rd = dict(modbusaddr=slaveId, switchStatus1 = r[0], switchStatus2 = r[1])
            logging.debug('采集(equipType={},equipId={})原始数据:{}'.format(equipType, equipID, r))
            logging.debug('采集(equipType={},equipId={})解析数据:{}'.format(equipType, equipID, rd))    
            # print('采集原始数据:', r) 
            # print('采集解析数据:', rd)
            return rd
        except Exception as e:
            logging.warning('采集(equipType={},equipId={},modbusaddr={})异常.'.format(equipType, equipID, slaveId))
            #测试
            if equipType == 1:
                return dict(modbusaddr=slaveId, humidity = 21.4, temperature = 43.8) 
            elif equipType == 2:
                return dict(modbusaddr=slaveId, switchStatus1 = 1, switchStatus2 = 1) 
        return {}

    def setSlaveData(self, equipType, equipID, slaveId, cmd, addr, value):
        try:
            if equipType == 2: # 继电器
                # execute(slave,功能代码,开始地址,quantity_of_x=0,output_value=0,data_format="",指定长度=-1)
                r = self.master.execute(slaveId, cmd, addr, output_value=value)
                # 0号开 10 05 00 00 FF 00 8f 7b
                # 0号关 10 05 00 00 00 00 ce 8b
                # 1号开 10 05 00 01 01 00 9e db
                # 1号关 10 05 00 01 00 00 9f 4b
                # 同时控制 10 0F 00 00 00 02 01 03 5e 56
                logging.info('设置(equipType={},equipId={},addr={},value={})结果:{}'.format(equipType, equipID, addr, value, r))
            return r
        except Exception as e:
            logging.info('设置(equipType={},equipId={},addr={},value={})异常.'.format(equipType, equipID, addr, value,))
        return None
