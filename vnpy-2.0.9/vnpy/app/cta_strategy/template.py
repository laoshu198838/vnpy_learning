""""""
from abc import ABC
from copy import copy
from typing import Any, Callable

from vnpy.trader.constant import Interval, Direction, Offset
from vnpy.trader.object import BarData, TickData, OrderData, TradeData
from vnpy.trader.utility import virtual

from .base import StopOrder, EngineType


class CtaTemplate(ABC):
    """"""

    author = ""
    parameters = []
    # 外部指定，配置窗口输入，
    variables = []
    # 内部缓存，自动缓存的一些变量
    # 这个地方最好只是放str\int\float\bool,而其他类型的变量参数放到init里面去
    # 这里的变量是类变量，只属于这个类的变量，实例化后不能访问

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ):
        """这里把cta引擎加载进去了，但是不知道怎么加载进去的"""
        self.cta_engine = cta_engine
        # 这个就是最开始使用的backtesting
        self.strategy_name = strategy_name
        self.vt_symbol = vt_symbol

        self.inited = False
        # 策略初始化好了之后才能变为True，主要是为计算指标加载需要的最少天数
        self.trading = False
        self.pos = 0

        # Copy a new variables list here to avoid duplicate insert when multiple
        # strategy instances are created with the same strategy class.
        self.variables = copy(self.variables)
        # 前后的self.variables是不一样的，后面这个是类的变量，前面那个是实例变量，可能是为了防止不同策略的之间的变量相互干扰
        # 浅复制，改变都会一起改变，增加不会一起增加
        self.variables.insert(0, "inited")
        self.variables.insert(1, "trading")
        self.variables.insert(2, "pos")
        # 这样子可以一直保持原来的那个变量可以是空的

        self.update_setting(setting)
        # 读出setting里面的字段，

    def update_setting(self, setting: dict):
        """
        Update strategy parameter with value in setting dict.
        """
        for name in self.parameters:
            if name in setting:
                setattr(self, name, setting[name])
                # 把参数名字设置到实例当中去
                # 默认的参数是在具体的策略实例当中的，当然你后期加载策略的时候也可以改

    #  classmethod 修饰符对应的函数不需要实例化
    @classmethod
    def get_class_parameters(cls):
        """
        Get default parameters dict of strategy class.
        这个cls表示所在的类Ctatemplate
        """
        class_parameters = {}
        for name in cls.parameters:
            class_parameters[name] = getattr(cls, name)
        return class_parameters
        # 获取cls的name对应的属性值

    def get_parameters(self):
        """
        Get strategy parameters dict.
        """
        strategy_parameters = {}
        for name in self.parameters:
            strategy_parameters[name] = getattr(self, name)
        return strategy_parameters

    def get_variables(self):
        """
        Get strategy variables dict.
        """
        strategy_variables = {}
        for name in self.variables:
            strategy_variables[name] = getattr(self, name)
        return strategy_variables

    def get_data(self):
        """
        Get strategy data.
        """
        strategy_data = {
            "strategy_name": self.strategy_name,
            "vt_symbol": self.vt_symbol,
            "class_name": self.__class__.__name__,
            "author": self.author,
            "parameters": self.get_parameters(),
            "variables": self.get_variables(),
        }
        return strategy_data

    # @virtual表示子类必须实现的方法，要不然不能实例化，
    # 这个是不是实盘才能用，感觉回测这个地方没有用到这个
    # @virtual表示这个函数是回调函数，当某件事情发生的时候他会调用这些函数
    # 但是不知道他是怎么把事件和函数关联起来的？？？
    @virtual
    def on_init(self):
        """
        Callback when strategy is inited.？？？
        """
        pass

    # 策略启动
    @virtual
    def on_start(self):
        """
        Callback when strategy is started.
        """
        pass

    # 策略停止
    @virtual
    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        pass

    # 行情推送
    @virtual
    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        pass

    # k线推送
    @virtual
    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        pass

    # 成交推送
    @virtual
    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        pass

    # 委托推送，国内一般是on_order优于on_trade
    @virtual
    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    # 成交推送
    @virtual
    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
    # 如何确定是哪一个订单下的
    def buy(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        Send buy order to open a long position.
        """
        return self.send_order(Direction.LONG, Offset.OPEN, price, volume, stop, lock)

    def sell(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        Send sell order to close a long position.
        """
        return self.send_order(Direction.SHORT, Offset.CLOSE, price, volume, stop, lock)

    def short(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        Send short order to open as short position.
        """
        return self.send_order(Direction.SHORT, Offset.OPEN, price, volume, stop, lock)

    def cover(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        Send cover order to close a short position.
        """
        return self.send_order(Direction.LONG, Offset.CLOSE, price, volume, stop, lock)

    def send_order(
        self,
        direction: Direction,
        offset: Offset,
        price: float,
        volume: float,
        stop: bool = False,
        lock: bool = False
    ):
        """
        Send a new order.
        """
        if self.trading:
            vt_orderids = self.cta_engine.send_order(
                self, direction, offset, price, volume, stop, lock
            )
        # //TODO:就是不知道这些参数是如何传入的
            return vt_orderids
        else:
            return []

    def cancel_order(self, vt_orderid: str):
        """
        Cancel an existing order.
        """
        if self.trading:
            self.cta_engine.cancel_order(self, vt_orderid)

    def cancel_all(self):
        """
        Cancel all orders sent by strategy.
        """
        if self.trading:
            self.cta_engine.cancel_all(self)

    def write_log(self, msg: str):
        """
        Write a log message.
        """
        self.cta_engine.write_log(msg, self)

    # 查询状态
    def get_engine_type(self):
        """
        Return whether the cta_engine is backtesting or live trading.
        """
        return self.cta_engine.get_engine_type()

    def load_bar(
        self,
        days: int,
        interval: Interval = Interval.MINUTE,
        callback: Callable = None,
        use_database: bool = False
    ):
        """
        Load historical bar data for initializing strategy.
        """
        if not callback:
            callback = self.on_bar  # 把on_bar里面的数据写入

        self.cta_engine.load_bar(
            self.vt_symbol,
            days,
            interval,
            callback,
            use_database
        )
        # 这里面的cta_engine是指回测的backtesting.py,从RQdata上面提取数据，调用ctaegine中的load_bar，这个加载的数据存在哪个地方呢，以什么形式，是从use_database的数据库里面取得数据的。

    def load_tick(self, days: int):
        """
        Load historical tick data for initializing strategy.
        """
        self.cta_engine.load_tick(self.vt_symbol, days, self.on_tick)

    def put_event(self):
        """
        Put an strategy data event for ui update.
        """
        if self.inited:
            self.cta_engine.put_strategy_event(self)

    def send_email(self, msg):
        """
        Send email to default receiver.
        """
        if self.inited:
            self.cta_engine.send_email(msg, self)

    # 同步数据
    def sync_data(self):
        """
        Sync strategy variables value into disk storage.
        """
        if self.trading:
            self.cta_engine.sync_strategy_data(self)


class CtaSignal(ABC):
    """"""

    def __init__(self):
        """"""
        self.signal_pos = 0

    @virtual
    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        pass

    @virtual
    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        pass

    def set_signal_pos(self, pos):
        """"""
        self.signal_pos = pos

    def get_signal_pos(self):
        """"""
        return self.signal_pos


class TargetPosTemplate(CtaTemplate):
    """"""
    tick_add = 1

    last_tick = None
    last_bar = None
    target_pos = 0
    vt_orderids = []

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(TargetPosTemplate, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )
        self.variables.append("target_pos")

    @virtual
    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.last_tick = tick

        if self.trading:
            self.trade()

    @virtual
    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.last_bar = bar

    @virtual
    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        vt_orderid = order.vt_orderid

        if not order.is_active() and vt_orderid in self.vt_orderids:
            self.vt_orderids.remove(vt_orderid)

    def set_target_pos(self, target_pos):
        """"""
        self.target_pos = target_pos
        self.trade()

    def trade(self):
        """"""
        self.cancel_all()

        pos_change = self.target_pos - self.pos
        if not pos_change:
            return

        long_price = 0
        short_price = 0

        if self.last_tick:
            if pos_change > 0:
                long_price = self.last_tick.ask_price_1 + self.tick_add
                if self.last_tick.limit_up:
                    long_price = min(long_price, self.last_tick.limit_up)
            else:
                short_price = self.last_tick.bid_price_1 - self.tick_add
                if self.last_tick.limit_down:
                    short_price = max(short_price, self.last_tick.limit_down)

        else:
            if pos_change > 0:
                long_price = self.last_bar.close_price + self.tick_add
            else:
                short_price = self.last_bar.close_price - self.tick_add

        if self.get_engine_type() == EngineType.BACKTESTING:
            if pos_change > 0:
                vt_orderids = self.buy(long_price, abs(pos_change))
            else:
                vt_orderids = self.short(short_price, abs(pos_change))
            self.vt_orderids.extend(vt_orderids)

        else:
            if self.vt_orderids:
                return

            if pos_change > 0:
                if self.pos < 0:
                    if pos_change < abs(self.pos):
                        vt_orderids = self.cover(long_price, pos_change)
                    else:
                        vt_orderids = self.cover(long_price, abs(self.pos))
                else:
                    vt_orderids = self.buy(long_price, abs(pos_change))
            else:
                if self.pos > 0:
                    if abs(pos_change) < self.pos:
                        vt_orderids = self.sell(short_price, abs(pos_change))
                    else:
                        vt_orderids = self.sell(short_price, abs(self.pos))
                else:
                    vt_orderids = self.short(short_price, abs(pos_change))
            self.vt_orderids.extend(vt_orderids)
