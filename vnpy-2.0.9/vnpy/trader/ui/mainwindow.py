"""
Implements main window of VN Trader.
"""

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

from vnpy.trader.ui.editor import CodeEditor
from vnpy.trader.engine import MainEngine
from vnpy.trader.utility import get_icon_path, TRADER_DIR
import sys

class MainWindow(QtWidgets.QMainWindow):
    """
    Main window of VN Trader.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(MainWindow, self).__init__()
        # 这两个参数在调用他们的时候传入了
        self.main_engine = main_engine
        self.event_engine = event_engine
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
        self.init_dock()
        self.init_toolbar()
        self.init_menu()
        self.load_window_setting("custom")

    def init_dock(self):
        """"""
        self.trading_widget, trading_dock = self.create_dock(
            TradingWidget, "交易", QtCore.Qt.LeftDockWidgetArea
        )
        tick_widget, tick_dock = self.create_dock(
            TickMonitor, "行情", QtCore.Qt.RightDockWidgetArea
        )
        order_widget, order_dock = self.create_dock(
            OrderMonitor, "委托", QtCore.Qt.RightDockWidgetArea
        )
        active_widget, active_dock = self.create_dock(
            ActiveOrderMonitor, "活动", QtCore.Qt.RightDockWidgetArea
        )
        trade_widget, trade_dock = self.create_dock(
            TradeMonitor, "成交", QtCore.Qt.RightDockWidgetArea
        )
        log_widget, log_dock = self.create_dock(
            LogMonitor, "日志", QtCore.Qt.BottomDockWidgetArea
        )
        account_widget, account_dock = self.create_dock(
            AccountMonitor, "资金", QtCore.Qt.BottomDockWidgetArea
        )
        position_widget, position_dock = self.create_dock(
            PositionMonitor, "持仓", QtCore.Qt.BottomDockWidgetArea
        )

        self.tabifyDockWidget(active_dock, order_dock)

        self.save_window_setting("default")

    def init_menu(self):
        """"""
        bar = self.menuBar()

        # System menu
        # 添加系统菜单名称
        sys_menu = bar.addMenu("系统")
        # 这些接口会在前面的某一个地方已经添加进去了
        gateway_names = self.main_engine.get_all_gateway_names()
        for name in gateway_names:
            # partial有延迟生效函数
            func = partial(self.connect, name)
            # 完成了图标、子目录、连接功能、绑定上级目录
            self.add_menu_action(sys_menu, f"连接{name}", "connect.ico", func)
        # 在此处加一条线进行区分
        sys_menu.addSeparator()
        # 创建退出子目录
        self.add_menu_action(sys_menu, "退出", "exit.ico", self.close)

        # App menu
        app_menu = bar.addMenu("功能")

        all_apps = self.main_engine.get_all_apps()
        for app in all_apps:
            # app.app_module是什么
            ui_module = import_module(app.app_module + ".ui")
            # 返回对象的属性
            widget_class = getattr(ui_module, app.widget_name)

            func = partial(self.open_widget, widget_class, app.app_name)
            icon_path = str(app.app_path.joinpath("ui", app.icon_name))
            # 添加菜单栏
            self.add_menu_action(
                app_menu, app.display_name, icon_path, func
            )
            # 添加工具栏
            self.add_toolbar_action(
                app.display_name, icon_path, func
            )

        # Global setting editor
        action = QtWidgets.QAction("配置", self)
        action.triggered.connect(self.edit_global_setting)
        # 如果菜单栏没有子级，直接用这个就可以了。
        bar.addAction(action)

        # Help menu
        help_menu = bar.addMenu("帮助")

        self.add_menu_action(
            help_menu,
            "查询合约",
            "contract.ico",
            partial(self.open_widget, ContractManager, "contract"),
        )
        self.add_toolbar_action(
            "查询合约",
            "contract.ico",
            partial(self.open_widget, ContractManager, "contract")
        )

        self.add_menu_action(
            help_menu,
            "代码编辑",
            "editor.ico",
            partial(self.open_widget, CodeEditor, "editor")
        )
        self.add_toolbar_action(
            "代码编辑",
            "editor.ico",
            partial(self.open_widget, CodeEditor, "editor")
        )

        self.add_menu_action(
            help_menu, "还原窗口", "restore.ico", self.restore_window_setting
        )

        self.add_menu_action(
            help_menu, "测试邮件", "email.ico", self.send_test_email
        )

        self.add_menu_action(
            help_menu, "社区论坛", "forum.ico", self.open_forum
        )
        self.add_toolbar_action(
            "社区论坛", "forum.ico", self.open_forum
        )

        self.add_menu_action(
            help_menu,
            "关于",
            "about.ico",
            partial(self.open_widget, AboutDialog, "about"),
        )

    def init_toolbar(self):
        """创建一个工具栏"""
        self.toolbar = QtWidgets.QToolBar(self)
        self.toolbar.setObjectName("工具栏")
        # 不能作为独立小窗口拖放
        self.toolbar.setFloatable(False)
        # 不能在主窗口范围内拖拽移动
        self.toolbar.setMovable(False)

        # Set button size
        w = 40
        size = QtCore.QSize(w, w)
        # 设置里面所有图标的大小
        self.toolbar.setIconSize(size)

        # Set button spacing
        self.toolbar.layout().setSpacing(10)
        # 添加工具栏的位置
        self.addToolBar(QtCore.Qt.LeftToolBarArea, self.toolbar)

    def add_menu_action(
        self,
        menu: QtWidgets.QMenu,
        action_name: str,
        icon_name: str,
        func: Callable,
    ):
        """创建目录中的子目录"""
        # 获取对应的图标
        icon = QtGui.QIcon(get_icon_path(__file__, icon_name))
        # 创建子目录
        action = QtWidgets.QAction(action_name, self)
        # 子目录连接对象
        action.triggered.connect(func)
        # 子目录与图表绑定
        action.setIcon(icon)
        # 把子目录添加到上级目录中
        menu.addAction(action)

    def add_toolbar_action(
        self,
        action_name: str,
        icon_name: str,
        func: Callable,
    ):
        """"""
        icon = QtGui.QIcon(get_icon_path(__file__, icon_name))

        action = QtWidgets.QAction(action_name, self)
        action.triggered.connect(func)
        action.setIcon(icon)

        self.toolbar.addAction(action)

    def create_dock(
        self, widget_class: QtWidgets.QWidget, name: str, area: int
    ):
        """
        Initialize a dock widget.
        """
        widget = widget_class(self.main_engine, self.event_engine)

        dock = QtWidgets.QDockWidget(name)
        dock.setWidget(widget)
        dock.setObjectName(name)
        dock.setFeatures(dock.DockWidgetFloatable | dock.DockWidgetMovable)
        self.addDockWidget(area, dock)
        return widget, dock

    def connect(self, gateway_name: str):
        """
        Open connect dialog for gateway connection.
        """
        dialog = self.connect_dialogs.get(gateway_name, None)
        if not dialog:
            dialog = ConnectDialog(self.main_engine, gateway_name)

        dialog.exec_()

    def closeEvent(self, event):
        """
        Call main engine close function before exit.
        """
        reply = QtWidgets.QMessageBox.question(
            self,
            "退出",
            "确认退出？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )

        if reply == QtWidgets.QMessageBox.Yes:
            for widget in self.widgets.values():
                widget.close()
            self.save_window_setting("custom")

            self.main_engine.close()

            event.accept()
        else:
            event.ignore()

    def open_widget(self, widget_class: QtWidgets.QWidget, name: str):
        """
        Open contract manager.
        """
        widget = self.widgets.get(name, None)
        if not widget:
            widget = widget_class(self.main_engine, self.event_engine)
            self.widgets[name] = widget
        # isinstance(object, classinfo)
        if isinstance(widget, QtWidgets.QDialog):
            widget.exec_()
        else:
            widget.show()

    def save_window_setting(self, name: str):
        """
        Save current window size and state by trader path and setting name.
        """
        settings = QtCore.QSettings(self.window_title, name)
        settings.setValue("state", self.saveState())
        settings.setValue("geometry", self.saveGeometry())

    def load_window_setting(self, name: str):
        """
        Load previous window size and state by trader path and setting name.
        """
        settings = QtCore.QSettings(self.window_title, name)
        state = settings.value("state")
        geometry = settings.value("geometry")

        if isinstance(state, QtCore.QByteArray):
            self.restoreState(state)
            self.restoreGeometry(geometry)

    def restore_window_setting(self):
        """
        Restore window to default setting.
        """
        self.load_window_setting("default")
        self.showMaximized()

    def send_test_email(self):
        """
        Sending a test email.
        """
        self.main_engine.send_email("VN Trader", "testing")

    def open_forum(self):
        """
        """
        webbrowser.open("https://www.vnpy.com/forum/")

    def edit_global_setting(self):
        """
        """
        dialog = GlobalDialog()
        dialog.exec_()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(MainEngine,EventEngine)
    main.show()

    sys.exit(app.exec_())
