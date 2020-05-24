
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from vnpy.trader.constant import Interval, Direction, Offset
from datetime import datetime, timedelta
import sys
from vnpy.app.cta_backtester.ui.widget import StatisticsMonitor

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
# 此处一个点和两个点的差别
from vnpy.trader.ui.editor import CodeEditor
from vnpy.trader.engine import MainEngine
from vnpy.trader.utility import get_icon_path, TRADER_DIR
import sys


class VnpyExercise(QtWidgets.QWidget):
    """ vnpy练习 """

    def __init__(self):
        super(VnpyExercise, self).__init__()
        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("CTA回测")

        # Setting Part
        # 创建下来列表框保存具体策略
        self.class_combo = QtWidgets.QComboBox()
        # self.class_combo.SelectedIndex=='AAA'
        # 输入文本框，单行文本
        self.symbol_line = QtWidgets.QLineEdit("IF88.CFFEX")
        # 供选择的回测周期
        self.interval_combo = QtWidgets.QComboBox()
        # 把已经存在的回测周期添加到下拉列表中
        for inteval in Interval:
            self.interval_combo.addItem(inteval.value)

        # 默认设置为截止到今天之前的三年
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=3 * 365)

        self.start_date_edit = QtWidgets.QDateEdit(
            QtCore.QDate(
                start_dt.year,
                start_dt.month,
                start_dt.day
            )
        )
        self.end_date_edit = QtWidgets.QDateEdit(
            QtCore.QDate.currentDate()
        )

        self.rate_line = QtWidgets.QLineEdit("0.000025")
        self.slippage_line = QtWidgets.QLineEdit("0.2")
        self.size_line = QtWidgets.QLineEdit("300")
        self.pricetick_line = QtWidgets.QLineEdit("0.2")
        self.capital_line = QtWidgets.QLineEdit("1000000")

        self.inverse_combo = QtWidgets.QComboBox()
        self.inverse_combo.addItems(["正向", "反向"])

        backtesting_button = QtWidgets.QPushButton("开始回测")
        # backtesting_button.clicked.connect(self.start_backtesting)

        optimization_button = QtWidgets.QPushButton("参数优化")
        # optimization_button.clicked.connect(self.start_optimization)

        self.result_button = QtWidgets.QPushButton("优化结果")
        # self.result_button.clicked.connect(self.show_optimization_result)
        self.result_button.setEnabled(False)

        downloading_button = QtWidgets.QPushButton("下载数据")
        # downloading_button.clicked.connect(self.start_downloading)

        self.order_button = QtWidgets.QPushButton("委托记录")
        # self.order_button.clicked.connect(self.show_backtesting_orders)
        self.order_button.setEnabled(False)

        self.trade_button = QtWidgets.QPushButton("成交记录")
        # self.trade_button.clicked.connect(self.show_backtesting_trades)
        self.trade_button.setEnabled(False)

        self.daily_button = QtWidgets.QPushButton("每日盈亏")
        # self.daily_button.clicked.connect(self.show_daily_results)
        self.daily_button.setEnabled(False)

        self.candle_button = QtWidgets.QPushButton("K线图表")
        # self.candle_button.clicked.connect(self.show_candle_chart)
        self.candle_button.setEnabled(False)

        edit_button = QtWidgets.QPushButton("代码编辑")
        # edit_button.clicked.connect(self.edit_strategy_code)

        reload_button = QtWidgets.QPushButton("策略重载")
        # reload_button.clicked.connect(self.reload_strategy_class)

        for button in [
            backtesting_button,
            optimization_button,
            downloading_button,
            self.result_button,
            self.order_button,
            self.trade_button,
            self.daily_button,
            self.candle_button,
            edit_button,
            reload_button
        ]:
            button.setFixedHeight(button.sizeHint().height() * 2)

        form = QtWidgets.QFormLayout()
        form.addRow("交易策略", self.class_combo)
        form.addRow("本地代码", self.symbol_line)
        form.addRow("K线周期", self.interval_combo)
        form.addRow("开始日期", self.start_date_edit)
        form.addRow("结束日期", self.end_date_edit)
        form.addRow("手续费率", self.rate_line)
        form.addRow("交易滑点", self.slippage_line)
        form.addRow("合约乘数", self.size_line)
        form.addRow("价格跳动", self.pricetick_line)
        form.addRow("回测资金", self.capital_line)
        form.addRow("合约模式", self.inverse_combo)

        result_grid = QtWidgets.QGridLayout()
        result_grid.addWidget(self.trade_button, 0, 0)
        result_grid.addWidget(self.order_button, 0, 1)
        result_grid.addWidget(self.daily_button, 1, 0)
        result_grid.addWidget(self.candle_button, 1, 1)

        # 垂直布局
        left_vbox = QtWidgets.QVBoxLayout()
        left_vbox.addLayout(form)
        left_vbox.addWidget(backtesting_button)
        left_vbox.addWidget(downloading_button)
        # 在此处进行一定的划分，相当于画一条横线
        left_vbox.addStretch()
        left_vbox.addLayout(result_grid)
        left_vbox.addStretch()
        left_vbox.addWidget(optimization_button)
        left_vbox.addWidget(self.result_button)
        left_vbox.addStretch()
        left_vbox.addWidget(edit_button)
        left_vbox.addWidget(reload_button)

        # Result part
        self.statistics_monitor = StatisticsMonitor()
        # self.statistics_monitor = QtWidgets.QTextEdit()
        # 和QLineEdit的区别就是，line只能是单行数据
        # QTextEdit显示多行文本内容，当文本内容超出控件显示范围时，可以显示水平和垂直滚动条。
        self.log_monitor = QtWidgets.QTextEdit()
        self.log_monitor.setMaximumHeight(400)

        self.chart = QtWidgets.QTextEdit()  # BacktesterChart()
        self.chart.setMinimumWidth(600)

        self.trade_dialog = QtWidgets.QTextEdit()
        # self.trade_dialog = BacktestingResultDialog(
        # self.main_engine,
        # self.event_engine,
        # "回测成交记录",
        # BacktestingTradeMonitor
        # )
        self.order_dialog = QtWidgets.QTextEdit()
        # self.order_dialog = BacktestingResultDialog(
        #     self.main_engine,
        #     self.event_engine,
        #     "回测委托记录",
        #     BacktestingOrderMonitor
        # )
        self.daily_dialog = QtWidgets.QTextEdit()
        # self.daily_dialog = BacktestingResultDialog(
        #     self.main_engine,
        #     self.event_engine,
        #     "回测每日盈亏",
        #     DailyResultMonitor
        # )

        # Candle Chart
        # self.candle_dialog = CandleChartDialog()

        # Layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.statistics_monitor)
        vbox.addWidget(self.log_monitor)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addLayout(left_vbox)
        hbox.addLayout(vbox)
        hbox.addWidget(self.chart)
        self.setLayout(hbox)


class StatisticsMonitor(QtWidgets.QTableWidget):
    """"""
    KEY_NAME_MAP = {
        "start_date": "首个交易日",
        "end_date": "最后交易日",

        "total_days": "总交易日",
        "profit_days": "盈利交易日",
        "loss_days": "亏损交易日",

        "capital": "起始资金",
        "end_balance": "结束资金",

        "total_return": "总收益率",
        "annual_return": "年化收益",
        "max_drawdown": "最大回撤",
        "max_ddpercent": "百分比最大回撤",

        "total_net_pnl": "总盈亏",
        "total_commission": "总手续费",
        "total_slippage": "总滑点",
        "total_turnover": "总成交额",
        "total_trade_count": "总成交笔数",

        "daily_net_pnl": "日均盈亏",
        "daily_commission": "日均手续费",
        "daily_slippage": "日均滑点",
        "daily_turnover": "日均成交额",
        "daily_trade_count": "日均成交笔数",

        "daily_return": "日均收益率",
        "return_std": "收益标准差",
        "sharpe_ratio": "夏普比率",
        "return_drawdown_ratio": "收益回撤比"
    }

    def __init__(self):
        """"""
        super().__init__()
        # 这个用来做什么的
        self.cells = {}

        self.init_ui()

    def init_ui(self):
        """"""
        self.setRowCount(len(self.KEY_NAME_MAP))
        self.resize(300, 700)
        # 设置每一行的行标题
        self.setVerticalHeaderLabels(list(self.KEY_NAME_MAP.values()))

        self.setColumnCount(1)
        # 让标题不可见
        self.horizontalHeader().setVisible(False)
        # 让大小自动适应布局的大小
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        # self.setEditTriggers(self.NoEditTriggers)
        # 填充表的内容
        for row, key in enumerate(self.KEY_NAME_MAP.keys()):
            cell = QtWidgets.QTableWidgetItem()
            self.setItem(row, 0, cell)
            self.cells[key] = cell


class MainWindow(QtWidgets.QMainWindow):
    """
    Main window of VN Trader.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(MainWindow, self).__init__()
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
        # self.init_toolbar()
        # self.init_menu()
        # self.load_window_setting("custom")

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
        
if __name__ == "__main__":
    app=QtGui.QApplication(sys.argv)
    main=MainWindow()
    main.show()
    app.exec_()
