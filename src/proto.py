import logging
import time
import struct
import serial
import modbus_tk.modbus_rtu as tkRtu
import gl


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

# 协议适配设备 HT_EQUIP_TYPE_JDRK_TEMPERATURE 、HT_EQUIP_TYPE_REMOTE_RELAY、HT_EQUIP_TYPE_MICRO_PRESSURE
class ModbusRtuCh(metaclass=MetaRegCls):
    protoType = 'mobus_rtu'
    baudrate, parity = 9600, 'N'

    def __init__(self, portName, rtutimeout):
        try:
            se = serial.Serial(port = portName, baudrate = self.baudrate, parity = self.parity, stopbits = 1, timeout = rtutimeout)
            self.master = tkRtu.RtuMaster(se)
            self.master.set_timeout(rtutimeout)
            self.msg_err = ""
        except Exception as e:
            self.master = None
            self.msg_err = e
            logging.warning('%s Open failed, %s'%(portName, e))

    def portName(self):
        return self.master._serial.name if self.master else ""

    def getSlaveData(self, equipType, equipId, slaveId, cmd, addr, num):
        try:
            r = None
            '''
            有毒气体qData一体记录数据
            通讯正常数据 {dataType='serial_device_data','equipType'=3, 'equipId'=5, 'modbusaddr'=1 ,'comStatus'=1,'value'= 0.0}
            通讯故障数据 {dataType='serial_device_data','equipType'=3, 'equipId'=6, 'modbusaddr'=2 ,'comStatus'=0}
            '''
            ret_dict = dict(dataType = 'serial_device_data',equipType = equipType, equipId = equipId, modbusaddr = slaveId)

            if equipType == gl.HT_EQUIP_TYPE_JDRK_TEMPERATURE: #温湿度
                # execute(slave,功能代码,开始地址,quantity_of_x=0,output_value=0,data_format="",指定长度=-1)
                r = self.master.execute(slaveId, cmd, addr, num, data_format=">2h")
                # 40001 湿度 humidity 转换系数 0.1  
                # 40002 温度 temperature 转换系数 0.1 
                rd = dict(comStatus = gl.COM_STATUS_NORMAL, humidity = r[0]/10., temperature = r[1]/10.)  
                ret_dict.update(rd)
            elif equipType == gl.HT_EQUIP_TYPE_REMOTE_RELAY: # 远程继电器
                r = self.master.execute(slaveId, cmd, addr, num)
                # 获取所有开关状态 10 01 00 00 00 08 3E 8d 响应 10 01 01 03 14 B5 
                # switchStatus1 switchStatus2
                # r = (1, 1, 0, 0, 0, 0, 0, 0)
                rd = dict(comStatus = gl.COM_STATUS_NORMAL, switchStatus1 = r[0], switchStatus2 = r[1])
                ret_dict.update(rd)
            elif equipType == gl.HT_EQUIP_TYPE_MICRO_PRESSURE: # 微差压传感器
                r = self.master.execute(slaveId, cmd, addr, num)
                # 电流范围 4-20ma 测量范围 -100-100pa  
                # 数据转换公式 d/3900*(20-4)+4 3900对应20ma的值v
                v = r[0] / 3900 * (20 - 4) + 4 # 计算对应电流
                pressure = (v - 4) * 200 / 20 - 100
                rd = dict(comStatus = gl.COM_STATUS_NORMAL, value = pressure)
                ret_dict.update(rd)
                logging.debug('计算r={}数据:v={}，pressure={}'.format(r[0], v, pressure))

        except Exception as e:
            dinfo = "[{},equipType={},equipId={},slaveId={},cmd={},addr={},num={}]".format(self.portName(), equipType, equipId, slaveId, cmd, addr, num)
            logging.debug("{} err:{}".format(dinfo, e))
            d = dict(comStatus = gl.COM_STATUS_ABNORMAL)
            ret_dict.update(d)

        return ret_dict

    def setSlaveData(self, equipType, equipId, slaveId, cmd, addr, value):
        logging.debug('设置 equipType={},equipId={},addr={},value={}'.format(equipType, equipId, addr, value))
        try:
            if equipType == gl.HT_EQUIP_TYPE_REMOTE_RELAY: # 继电器
                # execute(slave,功能代码,开始地址,quantity_of_x=0,output_value=0,data_format="",指定长度=-1)
                r = self.master.execute(slaveId, cmd, addr, output_value=value)
                # 0号开 10 05 00 00 FF 00 8f 7b
                # 0号关 10 05 00 00 00 00 ce 8b
                # 1号开 10 05 00 01 01 00 9e db
                # 1号关 10 05 00 01 00 00 9f 4b
                # 同时控制 10 0F 00 00 00 02 01 03 5e 56
            return r
        except Exception as e:
            logging.debug(str(e))
        return None
    
    def close(self):
        if self.master:
            self.master.close()

# 协议适配设备 HT_EQUIP_TYPE_HX_OZONE、HT_EQUIP_TYPE_HX_ETHANOL
class ModbusToxicGasChannel(metaclass=MetaRegCls):
    '''
    有毒气体传感器协议
    '''
    protoType = 'modbus_ascii_toxic_gas'
    baudrate, parity = 9600, 'N'

    def __init__(self, portName, timeout):
        try:
            self.master = serial.Serial(port=portName, baudrate=self.baudrate, parity=self.parity, stopbits = 1,timeout = timeout)
            self.caches = {} 
            self.msg_err = ""
        except Exception as e:
            self.master = None
            self.msg_err = e
            logging.warning('%s Open failed, %s'%(portName, e))

    def command(self, slaveId, cmd, addr):
        try:
            xcmd = ':{:02X}{:02X}{:04X}{:04X}'.format(slaveId, cmd, addr, 1)
            check_dat = slaveId + cmd + addr + 1
            check_dat = ((~check_dat) + 1) & 0xFF # LCR校验方法：1、数据求和 2、取256模 3、取反，然后加1
            xcmd += '{:02X}\r\n'.format(check_dat)
            xcmd = bytes(xcmd.encode('utf-8'))
            print('xcmd=', xcmd)
            self.master.write(xcmd)

            buf, exp = bytearray(), 15
            while exp:
                ret = self.master.read(exp)
                print('ret=',ret)
                if len(ret) == exp:
                    buf.extend(ret)
                    break
                else:
                    raise Exception('有毒气体未获足够数据')
                
            # :0103020231C7\r\n
            # 3A 30 31 30 33 30 32 30 32 33 31 43 37 0D 0A
            assert (0x3A == buf[0]), "有毒气体获取起始校验异常"
            assert (slaveId == int(buf[1:3])), "有毒气体获取地址校验异常"
            assert (cmd == int(buf[3:5])), "有毒气体获取命令校验异常"
            assert (0x02 == int(buf[5:7])), "有毒气体获取长度校验异常"
            #check_dat = sum([ord(x) for x in buf[1:11]]) & 0xFF + 1
            #assert (check_dat == int(buf[11:13])), "有毒气体获取数据校验异常"
            assert (buf[-2] == 0x0D and buf[-1] == 0x0A), "有毒气体数据结尾异常"

            return int(buf[7:11].decode('utf-8'), 16)
        except Exception as e:
            logging.debug(str(e))

        return None

    def cachedCmd(self, slaveId, cmd, addr, timeout):
        cache = self.caches.setdefault(cmd, {})
        # cache is a dict of slaveID with (data, time) elements
        cd = cache.get(slaveId, None)
        if cd and (time.time()-cd[1]) < timeout:
            return cd[0]
        #missed or expired
        ret = None
        _timeout = self.master.timeout
        for i in range(2):
            time.sleep(0.1)
            ret = self.command(slaveId, cmd, addr)
            if ret:
                cache[slaveId] = ret, time.time()
                logging.debug('第{}次获取精度为：{}'.format(i+1, ret))
                break
            else:
                self.master.timeout = max(self.master.timeout * 2, 4)
        self.master.timeout = _timeout
        return ret

    def getSlaveData(self, equipType, equipId, slaveId, cmd, addr, num):
        try:
            ret_dict = dict(dataType='serial_device_data', equipType = equipType, equipId = equipId, modbusaddr = slaveId)
            dinfo = "[{}, {}]".format(self.portName(), slaveId)
            # 1、刷新精度 （3分钟）
            units = 2    # 气体浓度的小数位数，默认2位小数
            ret = self.cachedCmd(slaveId, cmd, 0x0011, 180.) # 精度寄存器地址0x0011  UINT6 数据范围0-3 
            if ret:
                units = ret
                logging.debug('获取精度为:{}'.format(units))
            else:
                raise Exception("有毒气体读取精度失败: " + dinfo)

            time.sleep(0.2)
            # 2、获取浓度
            dat = self.command(slaveId, cmd, addr) # 气体浓度寄存器地址0x0000 实际浓度=浓度/10^（精度） 范围0-65535
            if dat != None:
                fv = float(dat)
                if units >= 0 and units <= 3:
                    fv /= pow(10, units)
                d = dict(comStatus = gl.COM_STATUS_NORMAL, value = fv)
                ret_dict.update(d)
            else:
                raise Exception("有毒气体获取浓度失败: " + dinfo)
        except Exception as e:
            logging.debug(str(e))
            d = dict(comStatus = gl.COM_STATUS_ABNORMAL)
            ret_dict.update(d)

        return ret_dict

    def portName(self):
        return self.master.name if self.master else ""

    def close(self):
        if self.master:
            self.master.close()

