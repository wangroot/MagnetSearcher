# -*- coding: UTF-8 -*-
# 爬虫
from PySide2.QtCore import QObject, Signal
from requests import session as RqSession
from re import findall, IGNORECASE
from queue import Queue
from threading import Thread
from lxml.etree import HTML
from node import Magnet
from constant import HEADERS


class Spider(QObject):
    """磁力爬虫"""
    thread_num = 10  # 线程数
    status_change = Signal()  # 搜索状态改变
    result_add = Signal(Magnet)  # 结果增加

    def __init__(self):
        super().__init__(None)
        self._status = False  # 没有在运行
        self._session = RqSession()  # 创建会话
        self._session.headers = HEADERS
        self._content = None  # 搜索内容
        self._detail_urls = Queue()  # 详情页队列
        self._stop = False  # 是否停止

    def setContent(self, content:str):
        """设置搜索内容"""
        self._content = content

    def stop(self):
        """停止运行"""
        self._stop = True

    def getContent(self) -> str:
        """获取搜索内容"""
        return self._content

    def getStatus(self) -> bool:
        """获取当前爬虫状态"""
        return self._status

    def clearQueue(self, queue:Queue) -> None:
        """清空队列"""
        try:
            item = queue.get(False)
            while item:
                item = queue.get(False)
        except:
            return

    def isRelated(self, title:str) -> bool:
        """结果是否与搜索内容相关"""
        pattern = ""
        for char in self._content:
            pattern += "{}.*".format(char)
        related = findall(pattern, title, IGNORECASE)
        if related:
            return True
        return False

    def runMagnet(self):
        """开始"""
        # 状态变更
        self._status = True
        self.status_change.emit()
        funcs = [self.searchUrlMagnetCilixingqiu, self.searchUrlMagnetCilifeng, self.searchMagnetUrlWuji, self.searchUrlMagnetBitcq, self.searchUrlMagnetZooqle]  # 所有搜索函数
        # 获取详情页url
        self.clearQueue(self._detail_urls)  # 清空详情页队列
        for func in funcs:
            Thread(target=lambda: func(self._content)).start()
        # 详情页爬取
        detail_threads = []
        for num in range(self.thread_num):
            thread = Thread(name="详情页线程{}".format(num+1), target=self.detailThreadRun)
            detail_threads.append(thread)
            thread.start()
        for thread in detail_threads:
            thread.join()
        # 状态变更
        self._status = False
        self.status_change.emit()
        self._stop = False

    def searchMagnetUrlWuji(self, content:str) -> None:
        """https://zh.0mag.net/"""
        try:
            domain_name = "无极磁链"
            search_url = "https://zh.0mag.net/search?q={}".format(content)
            search_response = self._session.get(url=search_url)
            urls = findall(r"https://zh\.0mag\.net/!.{4}", search_response.text)
            for url in urls:
                result = (domain_name, url)
                self._detail_urls.put(result)
        except: pass
        finally: return

    def searchUrlMagnetBitcq(self, content:str, page:int=1) -> None:
        """https://bitcq.com/"""
        try:
            domain_name = "BITCQ"
            search_url = "https://bitcq.com/search?q={}&page={}".format(content, page)
            search_response = self._session.get(url=search_url)
            html = HTML(search_response.text)
            trs = html.xpath("//table[@class='table table-hover']/tbody/tr")
            if trs and not self._stop:
                for tr in trs:
                    url = "https://bitcq.com" + tr.xpath("./td")[1].xpath("./a/@href")[0]
                    peers = int(tr.xpath("./td")[-1].xpath("./text()")[0].strip())
                    result = (domain_name, url, peers)
                    self._detail_urls.put(result)
                    self.searchUrlMagnetBitcq(content=content, page=page + 1)
        except: pass
        finally: return

    def searchUrlMagnetZooqle(self, content:str, page:int=1) -> None:
        """https://zooqle.com/"""
        try:
            domain_name = "Zooqle"
            search_url = "https://zooqle.com/search?pg={}&q={}".format(page, content)
            search_response = self._session.get(url=search_url)
            urls = findall(r"class=\" small\"\s*href=\"(.+?)\"", search_response.text)
            if urls and not self._stop:
                peers = findall(r"Seeders:\s*(\d+)\s*\|\s*Leechers:\s*(\d+)", search_response.text)
                for num in range(len(peers)):
                    peers[num] = int(peers[num][0].strip()) + int(peers[num][1].strip())
                results = list(zip(urls, peers))
                for num in range(len(results)):
                    result = (domain_name, "https://zooqle.com" + results[num][0], results[num][1])
                    self._detail_urls.put(result)
                self.searchUrlMagnetZooqle(content=content, page=page + 1)
        except: pass
        finally: return

    def searchUrlMagnetCilifeng(self, content:str, page:int=1) -> None:
        """http://www.cilifeng.me/"""
        try:
            domain_name = "磁力风"
            search_url = "http://www.cilifeng.me/search?word={}&page={}".format(content, page)
            search_response = self._session.get(url=search_url)
            html = HTML(search_response.text)
            lis = html.xpath("//ul[@class='alt']/li")
            if lis and not self._stop:
                for li in lis:
                    url = "http://www.cilifeng.me" + li.xpath(".//a/@href")[0].replace("../../..", "")
                    result = (domain_name, url)
                    self._detail_urls.put(result)
                self.searchUrlMagnetCilifeng(content=content, page=page + 1)
        except: pass
        finally: return

    def searchUrlMagnetCilixingqiu(self, content:str, page:int=1) -> None:
        """https://cilixingqiu.co/"""
        try:
            domain_name = "磁力星球"
            search_url = "https://cilixingqiu.co/s/{}/p/{}".format(content, page)
            search_response = self._session.get(url=search_url)
            if "相关链接" not in search_response.text and not self._stop:
                urls = findall(r"/h/.+?\"", search_response.text)
                for num in range(len(urls)):
                    urls[num] = "https://cilixingqiu.co" + urls[num][0:-2]
                    result = (domain_name, urls[num])
                    self._detail_urls.put(result)
                self.searchUrlMagnetCilixingqiu(content=content, page=page + 1)
        except: pass
        finally: return

    def detailThreadRun(self):
        """爬取详情页面的线程运行函数"""
        try:
            detail_url = self._detail_urls.get(timeout=3)
            while detail_url and not self._stop:
                if detail_url[0] == "无极磁链":
                    self.detailMagnetWuji(detail_url)
                elif detail_url[0] == "BITCQ":
                    self.detailMagnetBitcq(detail_url)
                elif detail_url[0] == "Zooqle":
                    self.detailMagnetZooqle(detail_url)
                elif detail_url[0] == "磁力风":
                    self.detailMagnetCilifeng(detail_url)
                elif detail_url[0] == "磁力星球":
                    self.detailMagnetCilixingqiu(detail_url)
                detail_url = self._detail_urls.get(timeout=3)
        except:
            pass

    def detailMagnetWuji(self, detail_url:tuple) -> None:
        web_name, url = detail_url
        detail_response = self._session.get(url=url)
        title = findall(r"<title>(.+?)</title>", detail_response.text.replace("\n", ""))[0].replace(" 磁力下载 - ØMagnet 无极磁链", "").strip()
        if self.isRelated(title):
            try:
                magnet = findall(r"type=\"text\" value=\"(.+?)\"", detail_response.text)[0].strip()
            except:
                magnet = None
            try:
                hash = findall(r"<dt>种子特征码 :</dt>\s*<dd>(.+?)</dd>", detail_response.text)[0].strip()
            except:
                hash = None
            try:
                size = findall(r"<dt>文件大小 :</dt> <dd>(.+?)</dd>", detail_response.text)[0].strip()
            except:
                size = ""
            try:
                create_time = findall(r"<dt>发布日期 :</dt>\s*<dd>(.+) .+</dd>", detail_response.text)[0].strip()
            except:
                create_time = ""
            result = Magnet(domain=web_name, title=title, size=size, create_time=create_time, hash_str=hash, magnet_content=magnet)
            self.result_add.emit(result)

    def detailMagnetBitcq(self, detail_url:tuple) -> None:
        web_name, url, download = detail_url
        detail_response = self._session.get(url=url)
        title = findall(r"bitcq.com\s*\|(.+?)</title>", detail_response.text)[0].strip()
        if self.isRelated(title):
            try:
                magnet = findall(r"href=\"(.+?)\"\s*target=\"_blank\"\s*class=\"btn btn-default btn-lg\"", detail_response.text)[0].strip()
            except:
                magnet = None
            try:
                size = findall(r"Size:\s*(.+)", detail_response.text)[0].strip()
            except:
                size = ""
            result = Magnet(domain=web_name, title=title, size=size, download=download, magnet_content=magnet)
            self.result_add.emit(result)

    def detailMagnetZooqle(self, detail_url:tuple) -> None:
        web_name, url, download = detail_url
        detail_response = self._session.get(url=url)
        title = findall(r"id=\"torname\">(.+?)<", detail_response.text)[0].strip()
        if self.isRelated(title):
            try:
                magnet = findall(r"<a rel=\"nofollow\" href=\"(.+?)\"", detail_response.text)[0].strip()
            except:
                magnet = None
            try:
                size = findall(r"title=\"File size\"></i>(.+?)<", detail_response.text)[0].strip()
            except:
                size = ""
            result = Magnet(domain=web_name, title=title, size=size, download=download, magnet_content=magnet)
            self.result_add.emit(result)

    def detailMagnetCilifeng(self, detail_url:tuple) -> None:
        web_name, url = detail_url
        detail_response = self._session.get(url=url)
        title = findall(r"<title>(.+)-磁链详细-磁力风</title>", detail_response.text)[0].strip()
        if self.isRelated(title):
            try:
                magnet = findall(r"href=\"(.+)\">点击打开磁链", detail_response.text)[0].strip()
            except:
                magnet = None
            try:
                size = findall(r"class=\"d-inline-block text-gray mr-3\">(.+?)<", detail_response.text)[1].strip()
            except:
                size = ""
            result = Magnet(domain=web_name, title=title, size=size, magnet_content=magnet)
            self.result_add.emit(result)

    def detailMagnetCilixingqiu(self, detail_url:tuple) -> None:
        web_name, url = detail_url
        detail_response = self._session.get(url=url)
        title = findall(r"class=\"crumb-item current\">(.+?)</span>", detail_response.text)[0].strip()
        if self.isRelated(title):
            try:
                hash = findall(r"<p><a class=\"blue-color\" href=\"(.+?)\"", detail_response.text)[0].strip()
            except:
                hash = None
            try:
                size = findall(r"文件大小：<strong>(.+?)</strong>", detail_response.text)[0].strip()
            except:
                size = ""
            try:
                create_time = findall(r"收录时间：<strong>(.+?)</strong>", detail_response.text)[0].strip()
            except:
                create_time = ""
            result = Magnet(domain=web_name, title=title, size=size, create_time=create_time, hash_str=hash)
            self.result_add.emit(result)


if __name__ == '__main__':
    pass