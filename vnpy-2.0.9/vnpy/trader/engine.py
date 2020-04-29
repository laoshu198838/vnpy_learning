"""
"""

import logging
import smtplib
import os
from abc import ABC
from datetime import datetime
from email.message import EmailMessage
from queue import Empty, Queue
from threading import Thread
from typing import Any, Sequence, Type

from vnpy.event import Event, EventEngine
from .app import BaseApp
from .event import (
    EVENT_TICK,
    EVENT_ORDER,
    EVENT_TRADE,
    EVENT_POSITION,
    EVENT_ACCOUNT,
    EVENT_CONTRACT,
    EVENT_LOG
)
from .gateway import BaseGateway
from .object import (
    CancelRequest,
    LogData,
    OrderRequest,
    SubscribeRequest,
    HistoryRequest
)
from .setting import SETTINGS
from .utility import get_folder_path, TRADER_DIR


class MainEngine:
    """
    Acts as the core of VN Trader.
    一个大的类来把策略、ctp行情、事件引擎combine起来

    ctaTemplate -> CtaEngine->mainEngine ->ctpgateway ->CtpT dApi, 传到C++封装的接口。返回的就是vtOrderID

    """

    def __init__(self, event_engine: EventEngine = None):
        """绑定事件引擎"""
        if event_engine:
            self.event_engine = event_engine  # 这个地方难道还可以绑到其他事件引擎
        else:
            self.event_engine = EventEngine()
        self.event_engine.start()

        self.gateways = {}  # 这个字典的key是借口名称，value是key对应的引擎
        self.engines = {}  # 传入的引擎
        self.apps = {}
        self.exchanges = []  # 交易所

        os.chdir(TRADER_DIR)    # Change working directory
        # 用于改变当前工作的目录，from .utility import get_folder_path, TRADER_DIR，是这个地方把这个值引导过来了
        # 也就是把Path.cwd转换成TRADER_DIR目录地址，此处为C:\Users\Administrator
        self.init_engines()     # Initialize function engines

    # 添加引擎
    def add_engine(self, engine_class: Any):
        """
        Add function engine.
        """
        engine = engine_class(self, self.event_engine)
        # 返回的是engine_class的一个实例对象，如返回EmailEngine，
        # 上面的self代表的是MainEngine，engine_class可以指BacktesterEngine或CtaEngine等。
        self.engines[engine.engine_name] = engine
        # 这样子就可以把引擎的名字和对应的引擎对应起来
        return engine

    # 添加网管，gateway就是交易场所的API对接网管，每次添加一个gateway，就添加了一个交易所名称
    def add_gateway(self, gateway_class: Type[BaseGateway]):
        """
        Add gateway：添加接口；
        这个函数传入CTPGateway，将传入的CTPGateway
        """

        gateway = gateway_class(self.event_engine)
        # //TODO:这个geteway_class是从外面传入的参数
        # 这里得到一个gateway_class（是CTPGateway之类，不是BaseGateway）的实例，实例的参数是init MainEngine的时候传入的event_engine

        self.gateways[gateway.gateway_name] = gateway
        # 这里的gateway.gateway_name指的是ctp，调用上面的实例的gateway_name属性，并作为字典的键
        # 这里得到了gateways字典，在下面的get_gateway函数要用，取出gateway。

        # Add gateway supported exchanges into engine
        # 取出gateway的exchanges类属性（列表，非实例属性），
        for exchange in gateway.exchanges:
            if exchange not in self.exchanges:
                self.exchanges.append(exchange)

        return gateway

    # 主要是指增加系统界面的功能模块
    def add_app(self, app_class: Type[BaseApp]):
        """
        Add app.
        添加上层应用
        """
        app = app_class()
        self.apps[app.app_name] = app

        engine = self.add_engine(app.engine_class)
        return engine

    # 初始化引擎
    def init_engines(self):
        """
        Init all engines.
        """
        self.add_engine(LogEngine)
        # 启动日志引擎
        self.add_engine(OmsEngine)
        # 启动订单管理系统
        self.add_engine(EmailEngine)
        # 启动邮箱管理系统

    # 写入日志
    def write_log(self, msg: str, source: str = ""):
        """
        Put log event with specific message.
        """
        # LogData继承自BaseData，BaseData有gateway_name，所以这里可以传gateway_name，得到LogData对象。
        # //TODO: 不知道这个函数在做什么
        log = LogData(msg=msg, gateway_name=source)
        event = Event(EVENT_LOG, log)
        # Event传入type和data
        self.event_engine.put(event)

    # 获得网管
    def get_gateway(self, gateway_name: str):
        """
        Return gateway object by name.
        作用是传入CtpGateway，从字典中取出CtpGateway实例，再返回这个实例，getway_name=
        """
        gateway = self.gateways.get(gateway_name, None)
        if not gateway:
            self.write_log(f"找不到底层接口：{gateway_name}")
        return gateway
        # 这个返回getaway表示这个gateway已经启动了，现在可以使用了。
        # 主要用于后面的send_order,subscibe

    # 获得引擎
    def get_engine(self, engine_name: str):
        """
        Return engine object by name.
        """
        engine = self.engines.get(engine_name, None)
        if not engine:
            self.write_log(f"找不到引擎：{engine_name}")
        return engine

    # 获得默认设置
    def get_default_setting(self, gateway_name: str):
        """
        Get default setting dict of a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.get_default_setting()
        return None

    # 获得所有引擎的名字
    def get_all_gateway_names(self):
        """
        Get all names of gatewasy added in main engine.
        """
        return list(self.gateways.keys())

    # 获得所有的APP
    def get_all_apps(self):
        """
        Get all app objects.
        """
        return list(self.apps.values())

    # 获得所有的交易所
    def get_all_exchanges(self):
        """
        Get all exchanges.
        """
        return self.exchanges

    # 连接到行情
    def connect(self, setting: dict, gateway_name: str):
        """
        Start connection of a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.connect(setting)

    # 合约订阅
    def subscribe(self, req: SubscribeRequest, gateway_name: str):
        """
        Subscribe tick data update of a specific gateway.
        根据传入的CtpGateway，调用get_gateway函数取出CtpGateway实例，然后订阅行情。
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.subscribe(req)
            # 调用CTPGateway实例的subscribe方法，而self.md_api.subscribe(req)的方法就是self.md_api.subscribe(req)，即底层API，而传入的参数是SubscribeRequest（一个类），应该是{self.symbol}.{self.exchange.value}这样的形式

    # 下单
    def send_order(self, req: OrderRequest, gateway_name: str):
        """
        Send new order request to a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.send_order(req)
        else:
            return ""

    # 取消订单
    def cancel_order(self, req: CancelRequest, gateway_name: str):
        """
        Send cancel order request to a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_order(req)

    # 批量下单
    def send_orders(self, reqs: Sequence[OrderRequest], gateway_name: str):
        """
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.send_orders(reqs)
        else:
            return ["" for req in reqs]

    # 批量取消订单
    def cancel_orders(self, reqs: Sequence[CancelRequest], gateway_name: str):
        """
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_orders(reqs)

    # 历史查询
    def query_history(self, req: HistoryRequest, gateway_name: str):
        """
        Send cancel order request to a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.query_history(req)
        else:
            return None

    # 关闭
    def close(self):
        """
        Make sure every gateway and app is closed properly before
        programme exit.
        """
        # Stop event engine first to prevent new timer event.
        self.event_engine.stop()

        for engine in self.engines.values():
            engine.close()

        for gateway in self.gateways.values():
            gateway.close()


class BaseEngine(ABC):
    """
    Abstract class for implementing an function engine.
    """

    def __init__(
        self,
        main_engine: MainEngine,
        event_engine: EventEngine,
        engine_name: str,
    ):
        """"""
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.engine_name = engine_name

    def close(self):
        """"""
        pass


class LogEngine(BaseEngine):
    """
    Processes log event and output with logging module.
    日志引擎
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(LogEngine, self).__init__(main_engine, event_engine, "log")

        if not SETTINGS["log.active"]:
            return

        self.level = SETTINGS["log.level"]

        self.logger = logging.getLogger("VN Trader")
        self.logger.setLevel(self.level)

        self.formatter = logging.Formatter(
            "%(asctime)s  %(levelname)s: %(message)s"
        )

        self.add_null_handler()

        if SETTINGS["log.console"]:
            self.add_console_handler()

        if SETTINGS["log.file"]:
            self.add_file_handler()

        self.register_event()

    def add_null_handler(self):
        """
        Add null handler for logger.
        """
        null_handler = logging.NullHandler()
        self.logger.addHandler(null_handler)

    def add_console_handler(self):
        """
        Add console output of log.
        """
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)

    def add_file_handler(self):
        """
        Add file output of log.
        """
        today_date = datetime.now().strftime("%Y%m%d")
        filename = f"vt_{today_date}.log"
        log_path = get_folder_path("log")
        file_path = log_path.joinpath(filename)

        file_handler = logging.FileHandler(
            file_path, mode="a", encoding="utf8"
        )
        file_handler.setLevel(self.level)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)

    def register_event(self):
        """"""
        self.event_engine.register(EVENT_LOG, self.process_log_event)

    def process_log_event(self, event: Event):
        """
        Process log event.
        """
        log = event.data
        self.logger.log(log.level, log.msg)


class OmsEngine(BaseEngine):
    """
    Provides order management system function for VN Trader.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(OmsEngine, self).__init__(main_engine, event_engine, "oms")

        self.ticks = {}
        self.orders = {}
        self.trades = {}
        self.positions = {}
        self.accounts = {}
        self.contracts = {}

        self.active_orders = {}

        self.add_function()
        self.register_event()

    def add_function(self):
        """Add query function to main engine."""
        self.main_engine.get_tick = self.get_tick
        self.main_engine.get_order = self.get_order
        self.main_engine.get_trade = self.get_trade
        self.main_engine.get_position = self.get_position
        self.main_engine.get_account = self.get_account
        self.main_engine.get_contract = self.get_contract
        # 
        self.main_engine.get_all_ticks = self.get_all_ticks
        self.main_engine.get_all_orders = self.get_all_orders
        self.main_engine.get_all_trades = self.get_all_trades
        self.main_engine.get_all_positions = self.get_all_positions
        self.main_engine.get_all_accounts = self.get_all_accounts
        self.main_engine.get_all_contracts = self.get_all_contracts
        self.main_engine.get_all_active_orders = self.get_all_active_orders

    def register_event(self):
        """"""
        self.event_engine.register(EVENT_TICK, self.process_tick_event)
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        self.event_engine.register(EVENT_POSITION, self.process_position_event)
        self.event_engine.register(EVENT_ACCOUNT, self.process_account_event)
        self.event_engine.register(EVENT_CONTRACT, self.process_contract_event)
        # 注册事件和事件对应的处理函数，当tick,order,contract等数据过来的时候，调用对应的处理事件self.ticks = {}
        # self.orders、self.trades、self.positions、self.accounts、self.contracts

    def process_tick_event(self, event: Event):
        """"""
        tick = event.data
        self.ticks[tick.vt_symbol] = tick
        # 这个应该是每次只能缓存一个tick_data

    def process_order_event(self, event: Event):
        """"""
        order = event.data
        self.orders[order.vt_orderid] = order

        # If order is active, then update data in dict.
        if order.is_active():
            self.active_orders[order.vt_orderid] = order
        # Otherwise, pop inactive order from in dict
        elif order.vt_orderid in self.active_orders:
            self.active_orders.pop(order.vt_orderid)

    def process_trade_event(self, event: Event):
        """"""
        trade = event.data
        self.trades[trade.vt_tradeid] = trade

    def process_position_event(self, event: Event):
        """"""
        position = event.data
        self.positions[position.vt_positionid] = position

    def process_account_event(self, event: Event):
        """"""
        account = event.data
        self.accounts[account.vt_accountid] = account

    def process_contract_event(self, event: Event):
        """"""
        contract = event.data
        self.contracts[contract.vt_symbol] = contract

    def get_tick(self, vt_symbol):
        """
        Get latest market tick data by vt_symbol.
        """
        return self.ticks.get(vt_symbol, None)

    def get_order(self, vt_orderid):
        """
        Get latest order data by vt_orderid.
        """
        return self.orders.get(vt_orderid, None)

    def get_trade(self, vt_tradeid):
        """
        Get trade data by vt_tradeid.
        """
        return self.trades.get(vt_tradeid, None)

    def get_position(self, vt_positionid):
        """
        Get latest position data by vt_positionid.
        """
        return self.positions.get(vt_positionid, None)

    def get_account(self, vt_accountid):
        """
        Get latest account data by vt_accountid.
        """
        return self.accounts.get(vt_accountid, None)

    def get_contract(self, vt_symbol):
        """
        Get contract data by vt_symbol.
        """
        return self.contracts.get(vt_symbol, None)  # ？？？

    def get_all_ticks(self):
        """
        Get all tick data.
        """
        return list(self.ticks.values())

    def get_all_orders(self):
        """
        Get all order data.
        """
        return list(self.orders.values())

    def get_all_trades(self):
        """
        Get all trade data.
        """
        return list(self.trades.values())

    def get_all_positions(self):
        """
        Get all position data.
        """
        return list(self.positions.values())

    def get_all_accounts(self):
        """
        Get all account data.
        """
        return list(self.accounts.values())

    def get_all_contracts(self):
        """
        Get all contract data.
        """
        return list(self.contracts.values())

    def get_all_active_orders(self, vt_symbol: str = ""):
        """
        Get all active orders by vt_symbol.

        If vt_symbol is empty, return all active orders.
        """
        if not vt_symbol:
            return list(self.active_orders.values())
        else:
            active_orders = [
                order
                for order in self.active_orders.values()
                if order.vt_symbol == vt_symbol
            ]
            return active_orders


class EmailEngine(BaseEngine):
    """
    Provides email sending function for VN Trader.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(EmailEngine, self).__init__(main_engine, event_engine, "email")

        self.thread = Thread(target=self.run)
        self.queue = Queue()
        self.active = False

        self.main_engine.send_email = self.send_email

    def send_email(self, subject: str, content: str, receiver: str = "395252848@qq.com"):
        """"""
        # Start email engine when sending first email.
        if not self.active:
            self.start()

        # Use default receiver if not specified.
        if not receiver:
            receiver = SETTINGS["email.receiver"]

        msg = EmailMessage()
        msg["From"] = SETTINGS["email.sender"]
        msg["To"] = SETTINGS["email.receiver"]
        msg["Subject"] = subject
        msg.set_content(content)

        self.queue.put(msg)

    def run(self):
        """"""
        while self.active:
            try:
                msg = self.queue.get(block=True, timeout=1)

                with smtplib.SMTP_SSL(
                    SETTINGS["email.server"], SETTINGS["email.port"]
                ) as smtp:
                    smtp.login(
                        SETTINGS["email.username"], SETTINGS["email.password"]
                    )
                    smtp.send_message(msg)
            except Empty:
                pass

    def start(self):
        """"""
        self.active = True
        self.thread.start()

    def close(self):
        """"""
        if not self.active:
            return

        self.active = False
        self.thread.join()
