from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
import socket
import json

def get_gateway_heart():
    SENDERIP = "192.168.1.110"
    MYPORT = 9898
    MYGROUP = '224.0.0.50'

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #allow multiple sockets to use the same PORT number
    sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    #Bind to the port that we know will receive multicast data
    sock.bind((SENDERIP,MYPORT))
    #tell the kernel that we are a multicast socket
    #sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
    #Tell the kernel that we want to add ourselves to a multicast group
    #The address for the multicast group is the third param
    status = sock.setsockopt(socket.IPPROTO_IP,
                             socket.IP_ADD_MEMBERSHIP,
                             socket.inet_aton(MYGROUP) + socket.inet_aton(SENDERIP));

    #sock.setblocking(0)
    #ts = time.time()
    data, addr = sock.recvfrom(1024)
    data_str=str(data,encoding='utf-8')
    token=json.loads(data_str).get('token')
    sock.close()
    return token

def get_token():
    ip_port_single = ("192.168.1.111", 9898)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    comd = {'cmd': 'discovery'}
    order = json.dumps(comd)
    s.sendto(bytes(order, encoding="utf-8"), ip_port_single)
    data,addr=s.recvfrom(1024)
    data_str=str(data,encoding='utf-8')
    token=json.loads(data_str).get('token')
    s.close()
    return token

def get_token_encrypty():
    #tok = get_token()  # 拿到当前token,要进行加密的内容
    tok = get_gateway_heart()
    print('->', tok)
    k = prpcrypt()
    key_encrypt = k.encrypt(tok)
    print('->', key_encrypt)
    return key_encrypt

class prpcrypt():
    def __init__(self, key='ukr80n8htuc1mmiz'):
        #self.key = b'\x0e\x41\x94\x60\xd6\x10\xa4\x73\x93\xa7\x1e\x77\x88\xf4\xec\xb5'
        self.key =bytes(key, encoding='utf-8')
        self.iv  = b'\x17\x99\x6d\x09\x3d\x28\xdd\xb3\xba\x69\x5a\x2e\x6f\x58\x56\x2e'
        self.mode = AES.MODE_CBC

    # 加密函数，如果text不足16位就用空格补足为16位，
    # 如果大于16当时不是16的倍数，那就补足为16的倍数。
    def encrypt(self, text):        #text是要加密的内容
        cryptor = AES.new(self.key, self.mode, self.iv)
        # 这里密钥key 长度必须为16（AES-128）,
        # 24（AES-192）,或者32 （AES-256）Bytes 长度
        # 目前AES-128 足够目前使用
        length = 16
        count = len(text)
        if count < length:
            add = (length - count)
            # \0 backspace
            text = text + ('\0' * add)
        elif count > length:
            add = (length - (count % length))
            text = text + ('\0' * add)

        self.ciphertext = cryptor.encrypt(bytes(text, encoding='utf-8'))
        # 因为AES加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题
        # 所以这里统一把加密后的字符串转化为16进制字符串
        return str(b2a_hex(self.ciphertext),encoding='utf-8')
        #return self.ciphertext

    # 解密后，去掉补足的空格用strip() 去掉 b'0000000000000000'
    def decrypt(self, text):
        cryptor = AES.new(self.key, self.mode, self.iv)
        plain_text = cryptor.decrypt(a2b_hex(text))
        return plain_text.rstrip('\0')


if __name__ == '__main__':
    pc = prpcrypt('ukr80n8htuc1mmiz')  # 初始化密钥
    e = pc.encrypt('1234567890abcdef')  # 加密
   # d = pc.decrypt(e)  # 解密
    print("加密:", e)
    #print("解密:", d)

    tok_encry = get_token_encrypty()
    print(tok_encry)