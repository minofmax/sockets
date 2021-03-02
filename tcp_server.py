# -*- coding: utf-8 -*-
import socket
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import traceback
from threading import Thread

import select

sys.path.append('/root/sockets')
from base_class import PacketHandler


class BaseTcp(object):
    """
    基本的tcp server实现, 即bind绑定端口
    listen监听端口, 等待客户端连接
    accept()是从accept队列获取socket连接
    tcp连接连接的过程：
    客户端连接服务端端口, 服务端收到SYN同步包, 会将这个SYN包放入SYN队列；
    服务端从SYN队列中获取SYN包，返回给客户端一个ACK+SYN包；
    客户端返回一个ACK包，服务端将socket放入一个accept队列；
    服务端调用accept()方法从accept队列里获取一个socket文件描述符。
    :return:
    """

    @staticmethod
    def base_tcp():
        # 指定协议
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 让端口可以重复使用
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 绑定端口,指定ip是建立TCP连接的源ip
        server.bind(('0.0.0.0', 9090))
        # 监听, 在服务器拒绝连接之前，操作系统可以挂起的最大连接数量
        server.listen(1)
        # 准备接受消息
        client_socket, address = server.accept()
        print(address)
        # 接收消息
        data = client_socket.recv(1024)
        print(data)
        client_socket.send('server recived msg'.encode('utf-8'))
        # 关闭socket
        client_socket.close()
        server.close()
        return data


class AsyncPacketHandlerTcp(object):
    def start_server(self):
        """
        多线程构造异步非阻塞tcp server，主要解决两类问题：分包和粘包, 采用的方案是用在数据包首部增加长度
        分包：在以太网协议规范里，数据链路层的帧长度是1500字节，而ip层最大数据包长度是65535，传输层和应用层往上的数据报长度是不受限的。但是，数据帧
        只能发送1500字节，所以数据包会被分包发送。
        粘包：如果你发送的数据很短，然后在很短的时间内发送多个很短的数据包，为了节约网络开销，会从buffer里组合之后一起发送。这样就会有粘包问题。
        粘包分包会发生的情况：
        粘包会发生的情况：
        1、要发送的数据大于TCP发送缓冲区剩余空间大小，将会发生拆包。
        2、待发送数据大于MSS（最大报文长度），TCP在传输前将进行拆包。
        3、要发送的数据小于TCP发送缓冲区的大小，TCP将多次写入缓冲区的数据一次发送出去，将会发生粘包。
        4、接收数据端的应用层没有及时读取接收缓冲区中的数据，将发生粘包。
        解决方案:
        1、发送端给每个数据包添加包首部，首部中应该至少包含数据包的长度，这样接收端在接收到数据后，通过读取包首部的长度字段，便知道每一个数据包的实际长度了。
        2、发送端将每个数据包封装为固定长度（不够的可以通过补0填充），这样接收端每次从接收缓冲区中读取固定长度的数据就自然而然的把每个数据包拆分开来。
        3、可以在数据包之间设置边界，如添加特殊符号，这样，接收端通过这个边界就可以将不同的数据包拆分开。
        :return:
        """
        host = '0.0.0.0'
        port = 8080
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(1)
        # mc = MsgContainer()
        while True:
            conn, addr = s.accept()
            print('接收到来自客户端：{}的请求'.format(addr))
            Thread(target=self.worker, args=(conn,)).start()
            # while True:
            #     data = conn.recv(10)
            #     if len(data) == 0:
            #         break
            #     mc.add_data(data)
            #     msgs = mc.get_all_msg()
            #     for msg in msgs:
            #         print(msg)
            #
            #     mc.clear_msg()
            #
            # conn.close()

    @staticmethod
    def worker(conn):
        mc = PacketHandler()
        while True:
            data = conn.recv(1024)
            if not data:
                break
            mc.add_data(data)
            msgs = mc.get_all_msg()
            for msg in msgs:
                print('接收到信息：{}'.format(msg))
            mc.clear_msg()
        conn.close()


class SelectNIOTcp(object):
    """
    用select模型
    """

    @staticmethod
    def select_tcp():
        host = '0.0.0.0'
        port = 8080

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(1024)

        inputs = [server]
        outputs = []

        while inputs:
            readable, writeable, exceptional = select.select(inputs, outputs, inputs)
            # 可读
            for s in readable:
                if s is server:
                    conn, addr = s.accept()
                    inputs.append(conn)
                else:
                    data = s.recv(1024)
                    if data:
                        print('msg:{}'.format(data.decode('utf-8')))
                        if s not in outputs:
                            outputs.append(s)
                    else:
                        # 数据已为空, 客户端可能已经断开了连接, 需要清理
                        if s in outputs:
                            outputs.remove(s)
                        inputs.remove(s)
                        s.close()
            # 处理可写数据
            for w in writeable:
                try:
                    w.send('收到数据'.encode('utf-8'))
                except Exception as e:
                    msg = traceback.format_exc()
                    print(msg)
                if w in outputs:
                    outputs.remove(w)

            # 处理异常
            for e in exceptional:
                inputs.remove(e)
                if e in outputs:
                    outputs.remove(e)
                e.close()


class EpollAIOTcp(object):
    """
    Epoll模型：只能在linux环境下调试
    """

    @staticmethod
    def epoll_tcp():
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', 8000))
        # accpet队列大小设置为100
        server_socket.listen(100)
        server_socket.setblocking(False)

        epoll = select.epoll()
        # 注册一个in事件，等待有数据可读
        epoll.register(server_socket.fileno(), select.EPOLLIN)

        try:
            # 保存连接，请求，和响应信息
            connections = {}
            while True:
                # 最多等待1秒钟时间，有事件返回事件列表
                events = epoll.poll(1)
                for fileno, event in events:
                    # 事件的句柄是server
                    if fileno == server_socket.fileno():
                        connection, address = server_socket.accept()
                        # 设置为非阻塞的
                        connection.setblocking(False)
                        # 新建的连接也注册读事件
                        epoll.register(connection.fileno(), select.EPOLLIN)
                        connections[connection.fileno()] = connection
                        # 不是server，那就是建立的连接，现在连接可读
                    elif event & select.EPOLLIN:
                        data = connections[fileno].recv(1024)
                        if data:
                            epoll.modify(fileno, select.EPOLLOUT)
                        else:
                            epoll.modify(fileno, 0)
                            connections[fileno].shutdown(socket.SHUT_RDWR)
                            del connections[fileno]

                    elif event & select.EPOLLOUT:
                        # 可写的事件被触发
                        clientsocket = connections[fileno]
                        clientsocket.send('收到数据'.encode(encoding='utf-8'))

                        # 需要回写的数据已经写完了,再次注册读事件
                        epoll.modify(fileno, select.EPOLLIN)
                    elif event & select.EPOLLHUP:
                        # 被挂起了，注销句柄，关闭连接，这时候，是客户端主动断开了连接
                        epoll.unregister(fileno)
                        if fileno in connections:
                            connections[fileno].close()
                            del connections[fileno]
        finally:
            epoll.unregister(server_socket.fileno())
            epoll.close()
            server_socket.close()


if __name__ == '__main__':
    # mc = MsgContainer()
    # data = mc.pack_msg('123')
    # print(data)
    # msg1 = '中国'
    # msg2 = '锄禾日当午'
    # for i in range(10):
    #     msg1 = msg1 * 2
    #     msg2 = msg2 * 2
    # msg1 = mc.pack_msg(msg1)
    # msg2 = mc.pack_msg(msg2)
    # mc.add_data(msg1)
    # mc.add_data(msg2)
    #
    # lst = mc.get_all_msg()
    # for item in lst:
    #     print(item)
    # start_server()
    # select_tcp()
    #EpollAIOTcp().epoll_tcp()
    SelectNIOTcp().select_tcp()
