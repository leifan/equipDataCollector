import socket
import json
import time


class udp_gw():
    '''
    网关下设备查询和控制
    '''
    def __init__(self, ip_gateway='192.168.8.109'):
        self.ip_port_zu43 = ('224.0.0.50', 4321)
        self.ip_port_single = (ip_gateway, 9898)
        self.ip_port_zu9898=('224.0.0.50', 9898)
    
    def setGatewayIp(self, ip_gateway):
        if ip_gateway != None:
            self.ip_port_single = (ip_gateway, 9898)

    def whois(self):
        '''
        以组播方式发送“whois”命令：
        {"cmd":"whois"}
        所有网关收到“whois”命令都要应答且回复自己的IP信息，以单播的形式回复：
        {'cmd': 'iam', 'protocal': 'UDP', 'port': '9898', 'sid': '50ec50c708fa', 
        'model': 'acpartner.v3', 'proto_version': '2.0.1', 'ip': '192.168.1.102'}
        '''
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        comd = {'cmd': 'whois'}
        order = json.dumps(comd)
        s.sendto(bytes(order, encoding="utf-8"), self.ip_port_zu43)
        data_bytes, addr = s.recvfrom(1024)
        data_dic = json.loads(str(data_bytes, encoding='utf-8'))
        s.close()
        return data_dic

    def get_id_list(self):
        '''
        查询子设备列表
        命令以单播方式发送给网关的UDP 9898端口，用来获取网关中有哪些子设备。
        以单播方式向网关发送“discovery”命令：
        {
        "cmd":"discovery"
        }

        响应
        {
        "cmd":"discovery_rsp",
        "sid":"50ec50c708fa",
        "token":"KyCWf8xsho23JOme",
        "dev_list":
        [
        {"sid":"158d000392613e","model":"plug"},
        {"sid":"158d00044d3c12","model":"weather"},
        {"sid":"158d0004563c17","model":"remote.b186acn01"}
        ]
        }
        '''
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        comd = {'cmd': 'discovery'}
        order = json.dumps(comd)
        s.sendto(bytes(order, encoding="utf-8"), self.ip_port_single)
        data_bytes, addr = s.recvfrom(1024)
        data_dic = json.loads(str(data_bytes, encoding='utf-8'))
        s.close()
        return data_dic

    def read_sid(self, sid):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        comd = {'cmd': 'read', 'sid': sid}
        order = json.dumps(comd)
        s.sendto(bytes(order, encoding="utf-8"), self.ip_port_single)
        data_bytes, addr = s.recvfrom(1024)
        data_dic = json.loads(str(data_bytes, encoding='utf-8'))
        s.close()
        return data_dic

    def read_all_sid(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        ls = self.get_id_list().get('dev_list')
        ls_sensor_state = []
        for sid in ls:
            comd = {'cmd': 'read', 'sid': sid['sid']}
            order = json.dumps(comd)
            s.sendto(bytes(order, encoding="utf-8"), self.ip_port_single)
            data_bytes, addr = s.recvfrom(1024)
            data_dic = json.loads(str(data_bytes, encoding='utf-8'))
            ls_sensor_state.append(data_dic)
        s.close()
        return ls_sensor_state

    def get_dict_model_sid(self):
        dic_gw = self.whois()
        ip_gateway = dic_gw.get('ip') # 获取网关IP
        self.setGatewayIp(ip_gateway)
        print('ip_gateway=', ip_gateway) 
        #ls = self.get_id_list().get('dev_list')
        ls = self.read_all_sid()
        print('ls=', ls)
        dic_model_sid = {}
        gateWaySid = dic_gw.get('sid')
        dic_model_sid['gateway_' + gateWaySid] = gateWaySid
        for dic in ls:
            model = dic.get('model')
            sid = dic.get('sid')
            dic_model_sid['{}_{}'.format(model, sid)] = sid
        return dic_model_sid


class GetGateWayInfo():
    '''
    获取局域网网关信息
    '''
    def __init__(self, senderIp = '0.0.0.0'):
        self.gateWay_list = []
        self.senderIp = senderIp

    def GetGatewayHeart(self):
        '''
        获取心跳包数据如下：
        {"cmd":"heartbeat","model":"acpartner.v3","sid":"50ec50c708fa","token":"VdcDlmz9KOALtG3F","params":[{"ip":"192.168.1.102"}]}
        {"cmd":"report","model":"weather","sid":"158d00045c946f","params":[{"temperature":2526}]}
        '''
        SENDERIP = "0.0.0.0"
        if self.senderIp != SENDERIP :
            SENDERIP = self.senderIp
        print('SENDERIP=',SENDERIP)
        MYPORT = 9898
        MYGROUP = '224.0.0.50'
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        #allow multiple sockets to use the same PORT number
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #Bind to the port that we know will receive multicast data
        sock.bind((SENDERIP,MYPORT))
        #tell the kernel that we are a multicast socket
        #sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        #Tell the kernel that we want to add ourselves to a multicast group
        #The address for the multicast group is the third param
        status = sock.setsockopt(socket.IPPROTO_IP,
                                socket.IP_ADD_MEMBERSHIP,
                                socket.inet_aton(MYGROUP) + socket.inet_aton(SENDERIP))
        #sock.setblocking(0)
        #ts = time.time()
        data_bytes, addr = sock.recvfrom(1024)
        sock.close()
        data_dic = json.loads(str(data_bytes, encoding='utf-8'))
        return data_dic
    
    def GetGateWayEquipInfo(self):
        '''
        获取网关信息列表
        抓5次包获取网关信息
        '''
        ip_list = []
        for i in range(6):
            m = self.GetGatewayHeart()
            print('第{}次心跳包:{}'.format(i+1, m))
            # {"cmd":"heartbeat","model":"acpartner.v3","sid":"50ec50c708fa","token":"VdcDlmz9KOALtG3F","params":[{"ip":"192.168.1.102"}]}
            if 'acpartner' in m.get('model'): # acpartner 为空调伴侣
                model = m.get('model')
                sid =  m.get('sid')
                ip = m.get('params')[0].get('ip')
                if ip not in ip_list:
                    print('获取网关ip:',ip)
                    self.gateWay_list.append({'model':model, 'sid':sid, 'ip':ip})

        return self.gateWay_list

if __name__=='__main__':
    print('开始获取网关信息')    
    gw_all = GetGateWayInfo()
    gateWay_list = gw_all.GetGateWayEquipInfo()
    print('获取网关信息：\n',gateWay_list)

    gw_list = []
    for a in gateWay_list:
        gw_list.append(udp_gw(a['ip']))

    while True:
        for gw in gw_list:
            time.sleep(5)
            a = gw.get_dict_model_sid()
            print('---',a)

    #{'plug': '158d000392613e', 'switch': '158d0001c10bd7', 'sensor_ht': '158d0001e87bd9',
    # 'magnet': '158d0001bb3daf', 'motion': '158d0001c2f110', 'gateway': '7811dcb38599'}

    # gw=udp_gw('192.168.1.111')
    # tmp = gw.read_sid('158d000392613e')
    # print(tmp)


    # time.sleep(5)
    # gw.write_plug('off')
    # time.sleep(5)
    # tmp=gw.read_sid('158d000392613e')
    # print(tmp)

    # time.sleep(5)
    # d = gw.write_plug('on')
    # print('write_plug->', d)
    # tmp=gw.read_sid('158d000392613e')
    # print(tmp)
