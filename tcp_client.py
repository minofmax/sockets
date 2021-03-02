# -*- coding: utf-8 -*-
import socket
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import time
from threading import Thread

sys.path.append('/root/sockets')

from base_class import PacketHandler


def connect_server():
    host = '127.0.0.1'
    port = 9090
    addr = (host, port)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 连接server
    client.connect(addr)
    # 向server发送数据
    client.send(b'I am client')
    revc = client.recv(1024)
    print(revc.decode(encoding='utf-8'))
    time.sleep(1)
    client.close()


mc = PacketHandler()


def start_client(addr, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((addr, port))
    s.send('解决分包问题'.encode('utf-8'))
    revc = s.recv(1024)
    print(revc.decode(encoding='utf-8'))
    s.send('解决粘包问题'.encode('utf-8'))
    revc = s.recv(1024)
    print(revc.decode(encoding='utf-8'))
    msg = '123' * 1000
    s.send(msg.encode('utf-8'))
    revc = s.recv(1024)
    print(revc.decode(encoding='utf-8'))
    s.close()


if __name__ == '__main__':
    # for i in range(5):
    #     Thread(target=connect_server).start()
    for i in range(1):
        print('start thread:{}'.format(i))
        Thread(target=start_client, args=('127.0.0.1', 8080,)).start()
    # start_client('127.0.0.1', 8080)
