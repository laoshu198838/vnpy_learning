import webbrowser
from functools import partial
from importlib import import_module
from typing import Callable

from PyQt5 import QtCore, QtGui, QtWidgets

from vnpy.event import EventEngine
from vnpy.trader.ui.widget import (
    TickMonitor,
    OrderMonitor,
    TradeMonitor,
    PositionMonitor,
    AccountMonitor,
    LogMonitor,
    ActiveOrderMonitor,
    ConnectDialog,
    ContractManager,
    TradingWidget,
    AboutDialog,
    GlobalDialog
)
from pathlib import Path

# 此处一个点和两个点的差别
from vnpy.trader.ui.editor import CodeEditor
from vnpy.trader.engine import MainEngine
from vnpy.trader.utility import get_icon_path, TRADER_DIR
import sys

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        """"""
        super(MainWindow, self).__init__()
        # 这两个参数在调用他们的时候传入了
    
        # 窗口的标题
        self.window_title = f"VN Trader [{TRADER_DIR}]"
        # 连接的对话框
        self.connect_dialogs = {}
        # 控件集合
        self.widgets = {}

        self.init_ui()
    
    def init_ui(self):
        """"""
        self.setWindowTitle(self.window_title)
        # self.init_dock()
        # self.init_toolbar()
        self.init_menu()
        # self.load_window_setting("custom")
    
    def init_menu(self):
        """"""
        bar = self.menuBar()

        # System menu
        sys_menu = bar.addMenu("系统")
        # 这些接口会在前面的某一个地方已经添加进去了
        gateway_names = ['连接CTP','连接CTPTEST']
        for name in gateway_names:
            func = partial(self.connect, name)
            self.add_menu_action(sys_menu, f"连接{name}", "connect.ico", func)

        sys_menu.addSeparator()

        self.add_menu_action(sys_menu, "退出", "exit.ico", self.close)

        # App menu
        app_menu = bar.addMenu("功能")

        # all_apps = ['CTA策略','CTA回测']
        # for app in all_apps:
        #     ui_module = import_module(app.app_module + ".ui")
        #     widget_class = getattr(ui_module, app.widget_name)

        #     func = partial(self.open_widget, widget_class, app.app_name)
        #     icon_path = str(app.app_path.joinpath("ui", app.icon_name))
        #     self.add_menu_action(
        #         app_menu, app.display_name, icon_path, func
        #     )
        #     self.add_toolbar_action(
        #         app.display_name, icon_path, func
            # )

        # Global setting editor
        # action = QtWidgets.QAction("配置", self)
        # action.triggered.connect(self.edit_global_setting)
        # bar.addAction(action)

        # Help menu
        help_menu = bar.addMenu("帮助")

        # self.add_menu_action(
        #     help_menu,
        #     "查询合约",
        #     "contract.ico",
        #     partial(self.open_widget, ContractManager, "contract"),
        # )
        # self.add_toolbar_action(
        #     "查询合约",
        #     "contract.ico",
        #     partial(self.open_widget, ContractManager, "contract")
        # )

        # self.add_menu_action(
        #     help_menu,
        #     "代码编辑",
        #     "editor.ico",
        #     partial(self.open_widget, CodeEditor, "editor")
        # )
        # self.add_toolbar_action(
        #     "代码编辑",
        #     "editor.ico",
        #     partial(self.open_widget, CodeEditor, "editor")
        # )

        # self.add_menu_action(
        #     help_menu, "还原窗口", "restore.ico", self.restore_window_setting
        # )

        # self.add_menu_action(
        #     help_menu, "测试邮件", "email.ico", self.send_test_email
        # )

        # self.add_menu_action(
        #     help_menu, "社区论坛", "forum.ico", self.open_forum
        # )
        # self.add_toolbar_action(
        #     "社区论坛", "forum.ico", self.open_forum
        # )

        # self.add_menu_action(
        #     help_menu,
        #     "关于",
        #     "about.ico",
        #     partial(self.open_widget, AboutDialog, "about"),
        # )
    def add_menu_action(
        self,
        menu: QtWidgets.QMenu,
        action_name: str,
        icon_name: str,
        func: Callable,
    ):
        """"""
        icon = QtGui.QIcon(get_icon_path(__file__, icon_name))

        action = QtWidgets.QAction(action_name, self)
        action.triggered.connect(func)
        action.setIcon(icon)

        menu.addAction(action)

    def connect(self, gateway_name: str):
        """
        Open connect dialog for gateway connection.
        """
        dialog = self.connect_dialogs.get(gateway_name, None)
        if not dialog:
            dialog = ConnectDialog(self.main_engine, gateway_name)

        dialog.exec_()

def get_icon_path(filepath: str, ico_name: str):
    """
    Get path for icon file with ico name.
    """
    ui_path = Path(filepath).parent
    print(ui_path)
    icon_path = ui_path.joinpath("ico", ico_name)
    return str(icon_path)    


if __name__ == "__main__":
    # app = QtWidgets.QApplication(sys.argv)
    # main = MainWindow()
    # main.show()
    print(get_icon_path(__file__, 'connect.ico'))
    # sys.exit(app.exec_())
