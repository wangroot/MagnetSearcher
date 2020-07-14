import sys
from PySide2.QtWidgets import QApplication, QTableWidgetItem, QMenu
from PySide2.QtCore import QFile, Slot, Qt
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import QCursor, QIcon
from threading import Thread, Lock
from re import findall
from spider import Spider
from node import Magnet
from constant import *


class Main(object):
    """主程序"""
    def __init__(self):
        self.loadIni()  # 加载配置文件
        self.app = QApplication(sys.argv)
        self.loadUi()  # 加载ui
        self.attribute()  # 属性
        self.connect()  # 槽连接
        self.window.show()
        sys.exit(self.app.exec_())

    def loadIni(self):
        """获取配置文件"""
        with open(RESOURCES_ROOT + "/setting.ini", "r") as file:
            text = file.read()
            thread_num = int(findall(r"thread_num = (\d+);", text)[0])
            Spider.thread_num = thread_num

    def attribute(self):
        """属性"""
        # 图标
        self.window.setWindowIcon(QIcon(RESOURCES_ROOT + "/magnet.ico"))
        # 磁力爬虫
        self.spider = Spider()
        self.spider_thread = None
        # 爬虫线程锁
        self.lock = Lock()
        # 右键菜单
        self.rightMenu = QMenu(self.window.search_out)
        # 剪切板
        self.clipboard = QApplication.clipboard()

    def loadUi(self):
        """加载ui文件"""
        # 主ui
        ui = QFile(UI_ROOT + "/main.ui")
        ui.open(QFile.ReadOnly)
        ui.close()
        self.window = QUiLoader().load(ui)

    def connect(self):
        """槽连接"""
        # 搜索框和按钮
        self.window.search_button.clicked.connect(self.search)
        self.window.input_box.returnPressed.connect(self.search)
        # 磁力搜索线程
        self.spider.status_change.connect(self.searchStatusChange)
        self.spider.result_add.connect(self.outputBoxAdd)
        # 右键菜单
        action = self.rightMenu.addAction("复制")
        action.triggered.connect(self.rightCopy)
        self.window.search_out.setContextMenuPolicy(Qt.CustomContextMenu)
        self.window.search_out.customContextMenuRequested.connect(lambda: self.rightMenu.exec_(QCursor.pos()))

    def searchStatusChange(self):
        """爬虫运行状态改变"""
        status = self.spider.getStatus()
        if status:  # 如果爬虫运行中
            self.window.search_status.setText("运行中")
            self.window.search_button.setText("停止")
        else:
            self.window.search_status.setText("未运行")
            self.window.search_button.setText("搜索")

    @Slot(Magnet)
    def outputBoxAdd(self, result:Magnet):
        """磁力增加到GUI"""
        self.lock.acquire()
        # 计数以及表格行数变更
        count = self.window.search_out.rowCount()
        result.id_num = count + 1
        self.window.search_out.setRowCount(count+1)
        # 设置值
        self.window.search_out.setItem(count, 0, QTableWidgetItem(result.domain))
        self.window.search_out.setItem(count, 1, QTableWidgetItem(result.title))
        self.window.search_out.setItem(count, 2, QTableWidgetItem(result.size))
        self.window.search_out.setItem(count, 3, QTableWidgetItem(result.download))
        self.window.search_out.setItem(count, 4, QTableWidgetItem(result.create_time))
        self.lock.release()

    def search(self):
        """搜索"""
        bt_text = self.window.search_button.text()
        if bt_text == "搜索":
            # 删除原有的
            Magnet.all.clear()
            self.window.search_out.setRowCount(0)
            self.window.search_out.clearContents()
            # 搜索
            content = self.window.input_box.text()
            if content:
                self.spider.setContent(content)
                self.spider_thread = Thread(target=self.spider.runMagnet)
                self.spider_thread.start()
        else:  # 停止
            self.spider.stop()

    def rightCopy(self):
        """右键菜单：复制"""
        try:
            select_item = self.window.search_out.selectedItems()[0]
            row = select_item.row()
            for magnet in Magnet.all:
                if magnet.id_num == row+1:
                    if magnet.hash:
                        self.clipboard.setText(magnet.hash)
                    elif magnet.magnet_content:
                        self.clipboard.setText(magnet.magnet_content)
                    else:
                        self.clipboard.setText(magnet.torrent)
                    break
        except: pass


if __name__ == '__main__':
    Main()