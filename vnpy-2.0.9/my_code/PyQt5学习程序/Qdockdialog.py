import csv
from enum import Enum
from typing import Any
from copy import copy

from PyQt5 import QtCore, QtGui, QtWidgets

from vnpy.event import Event, EventEngine
from vnpy.trader.constant import Direction, Exchange, Offset, OrderType
from vnpy.trader.engine import MainEngine
from vnpy.trader.event import (
    EVENT_TICK,
    EVENT_TRADE,
    EVENT_ORDER,
    EVENT_POSITION,
    EVENT_ACCOUNT,
    EVENT_LOG
)
from vnpy.trader.object import OrderRequest, SubscribeRequest
from vnpy.trader.utility import load_json, save_json
from vnpy.trader.setting import SETTING_FILENAME, SETTINGS
from PyQt5.QtWidgets import (
    QDesktopWidget,
    QMainWindow,
    QApplication
)

from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine

from vnpy.trader.utility import get_icon_path, TRADER_DIR
import sys
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
    GlobalDialog,
    BaseMonitor,
    BaseCell,
    EnumCell,
    BidCell,
    AskCell,
    TimeCell
)

from vnpy.trader.ui.editor import CodeEditor
from vnpy.trader.engine import MainEngine
from vnpy.trader.utility import get_icon_path, TRADER_DIR
import sys
from vnpy.app.cta_strategy import CtaStrategyApp


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
            LogMonitor, "日志", QtCore.Qt.LeftDockWidgetArea
        )
        account_widget, account_dock = self.create_dock(
            AccountMonitor, "资金", QtCore.Qt.BottomDockWidgetArea
        )
        position_widget, position_dock = self.create_dock(
            PositionMonitor, "持仓", QtCore.Qt.BottomDockWidgetArea
        )

        self.tabifyDockWidget(active_dock, order_dock)

        self.save_window_setting("default")

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

    def save_window_setting(self, name: str):
        """
        Save current window size and state by trader path and setting name.
        """
        # 创建一个 Qsettings的对象时，我们需要传递给它两个参数，第一个是你公司或者组织的名称，第二个事你的应用程序的名称

        settings = QtCore.QSettings(self.window_title, name)
        settings.setValue("state", self.saveState())
        settings.setValue("geometry", self.saveGeometry())

    def init_menu(self):
        """"""
        bar = self.menuBar()

        # System menu
        # 添加系统菜单名称
        sys_menu = bar.addMenu("系统")

        gateway_names = self.main_engine.get_all_gateway_names()
        for name in gateway_names:
            # partial有延迟生效函数，那他怎么知道什么时候生效呢！！
            func = partial(self.connect, name)
            # 完成了图标、子目录、连接功能、绑定上级目录
            self.add_menu_action(sys_menu, f"连接{name}", "connect.ico", func)
        # 在此处加一条线进行区分
        sys_menu.addSeparator()
        # 创建退出子目录，self.close是退出当前界面！！
        self.add_menu_action(sys_menu, "退出", "exit.ico", self.close)

        app_menu = bar.addMenu("功能")
        self.main_engine.add_app(CtaStrategyApp)
        all_apps = self.main_engine.get_all_apps()
        for app in all_apps:
            # app.app_module获取对象来自哪个模块，如vnpy.event.engine
            print(app.app_module+'.ui')
            ui_module = import_module(app.app_module + ".ui")
            # 返回对象的属性，即名称
            # print(getattr(ui_module, app.widget_name))
            # <class 'vnpy.app.cta_strategy.ui.widget.CtaManager'>
            widget_class = getattr(ui_module, app.widget_name)

            func = partial(self.open_widget, widget_class, app.app_name)
            # 获取icon的地址
            icon_path = str(app.app_path.joinpath("ui", app.icon_name))
            # 添加菜单栏
            self.add_menu_action(
                app_menu, app.display_name, icon_path, func
            )
            # 添加工具栏
            self.add_toolbar_action(
                app.display_name, icon_path, func
            )


        action = QtWidgets.QAction("配置", self)
        action.triggered.connect(self.edit_global_setting)
        # 如果菜单栏没有子级，直接用这个就可以了。
        bar.addAction(action)

        help_menu = bar.addMenu("帮助")

    def init_toolbar(self):
        """创建一个工具栏"""
        self.toolbar = QtWidgets.QToolBar(self)
        self.toolbar.setObjectName("工具栏")
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)

        w = 40
        size = QtCore.QSize(w, w)
        self.toolbar.setIconSize(size)

        self.toolbar.layout().setSpacing(10)
        self.addToolBar(QtCore.Qt.LeftToolBarArea, self.toolbar)

    def load_window_setting(self, name: str):
        """
        Load previous window size and state by trader path and setting name.
        """
        settings = QtCore.QSettings(self.window_title, name)
        state = settings.value("state")
        geometry = settings.value("geometry")

        # 获取一个空的字节数组
        if isinstance(state, QtCore.QByteArray):
            self.restoreState(state)
            self.restoreGeometry(geometry)

    def edit_global_setting(self):
        """
        """
        dialog = GlobalDialog()
        dialog.exec_()

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
        # 创建子目录，这个地方有一个self不知道什么意思
        action = QtWidgets.QAction(action_name, self)
        # 子目录连接对象
        action.triggered.connect(func)
        # 子目录与图表绑定
        action.setIcon(icon)
        # 把子目录添加到上级目录中,菜单栏有默认位置，可以不传位置
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    main = MainWindow(main_engine, event_engine)
    main.show()

    sys.exit(app.exec_())
