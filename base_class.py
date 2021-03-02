# -*- coding: utf-8 -*-
ZERO_COUNT = 5


class PacketHandler(object):
    """
    靠首部增加五位，如‘00005’，来标记这次发送的数据报文长度是5
    """
    def __init__(self):
        self.msg = []
        self.msg_pond = b''
        self.msg_len = 0

    def __add_zero(self, str_len):
        head = (ZERO_COUNT - len(str_len)) * '0' + str_len
        return head.encode('utf-8')

    def pack_msg(self, data):
        """
        封装数据
        :param data:
        :return:
        """
        bdata = data.encode('utf-8')
        str_len = str(len(bdata))
        return self.__add_zero(str_len) + bdata

    def __get_msg_len(self):
        self.msg_len = int(self.msg_pond[:5])

    def add_data(self, data):
        if len(data) == 0 or data is None:
            return
        self.msg_pond += data
        self.__check_head()

    def __check_head(self):
        if len(self.msg_pond) > 5:
            self.__get_msg_len()
            self.__get_msg()

    def __get_msg(self):
        if len(self.msg_pond) - 5 >= self.msg_len:
            msg = self.msg_pond[5:5 + self.msg_len]
            self.msg_pond = self.msg_pond[5 + self.msg_len:]
            self.msg_len = 0
            msg = msg.decode('utf-8')
            self.msg.append(msg)
            self.__check_head()

    def get_all_msg(self):
        return self.msg

    def clear_msg(self):
        self.msg = []
