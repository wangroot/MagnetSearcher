# -*- coding: UTF-8 -*-
# 节点


class Magnet(object):
    """磁力"""
    all = []

    def __init__(self, id_num:int=None, domain:str="", title:str="", size:str="", download:int=0, create_time:str="", hash_str:str=None, magnet_content=None, torrent:str=None):
        self.id_num = id_num  # id
        self.domain = domain  # 来源
        self.title = title  # 标题
        self.size = size  # 大小
        self.download = download  # 下载量
        self.create_time = create_time  # 收录时间
        self.hash = hash_str  # 哈希
        self.magnet_content = magnet_content  # 磁力链接
        self.torrent = torrent  # 种子链接
        self.all.append(self)

    def __str__(self):
        out_str = "id_num:{}\ndomain:{}\ntitle:{}\nsize:{}\ndownload:{}\ncreate_time:{}\nhash:{}\nmagnet_content:{}\ntorrent:{}\n".format(self.id_num, self.domain, self.title, self.size, self.download, self.create_time, self.hash, self.magnet_content, self.torrent)
        return out_str


if __name__ == '__main__':
    pass