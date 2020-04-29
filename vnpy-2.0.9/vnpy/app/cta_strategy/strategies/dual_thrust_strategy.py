from datetime import time
from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)


class DualThrustStrategy(CtaTemplate):
    """"""

    author = "用Python的交易员"

    fixed_size = 1
    k1 = 0.4
    k2 = 0.6

    bars = []
    #主要用于缓存k线对象，因为我们主要是用k线进行回测

    day_open = 0
    day_high = 0
    day_low = 0

    range = 0
    long_entry = 0
    short_entry = 0
    exit_time = time(hour=14, minute=55)

    long_entered = False
    short_entered = False

    parameters = ["k1", "k2", "fixed_size"]
    variables = ["range", "long_entry", "short_entry"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()
        self.bars = []#虽然上面已经定义了bars=[],但是这个地方还需要再定义，以免在同时在跑多个策略时，多个策略使用同一个变量，使得策略混乱

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.cancel_all()

        self.bars.append(bar)
        # 缓存k线
        if len(self.bars) <= 2:
            return
        else:
            self.bars.pop(0)
        last_bar = self.bars[-2]
        # 判断是否是另外一天
        if last_bar.datetime.date() != bar.datetime.date():
            if self.day_high:
                self.range = self.day_high - self.day_low
                self.long_entry = bar.open_price + self.k1 * self.range
                self.short_entry = bar.open_price - self.k2 * self.range

            self.day_open = bar.open_price
            self.day_high = bar.high_price
            self.day_low = bar.low_price

            self.long_entered = False
            self.short_entered = False
        else:
            self.day_high = max(self.day_high, bar.high_price)
            self.day_low = min(self.day_low, bar.low_price)

        if not self.range:
            return
        # 有可能有异常情况，对于最高价和最低价是一样的情况，就立即退出。
        # self.exit_time不一定是整数点3点钟
        if bar.datetime.time() < self.exit_time:
            if self.pos == 0:
                if bar.close_price > self.day_open:
                    if not self.long_entered:
                        self.buy(self.long_entry, self.fixed_size, stop=True)#stop表示停止单，stop=False时，表示的是限价单
                else:
                    if not self.short_entered:
                        self.short(self.short_entry,
                                   self.fixed_size, stop=True)

            elif self.pos > 0:
                self.long_entered = True
                # 此处表示每天做多只能做一次
                self.sell(self.short_entry, self.fixed_size, stop=True)
                # 这个是一个止损单，当价格低于这个价格的时候他就会执行。然后立即开一个空头仓位
                # stop=True表示停止单，默认为false表示限价单
                if not self.short_entered:
                    self.short(self.short_entry, self.fixed_size, stop=True)

            elif self.pos < 0:
                self.short_entered = True

                self.cover(self.long_entry, self.fixed_size, stop=True)

                if not self.long_entered:
                    self.buy(self.long_entry, self.fixed_size, stop=True)

        else:
            # 时间一过某个时点，就会在当天用市价单平掉当天的仓位。
            if self.pos > 0:
                self.sell(bar.close_price * 0.99, abs(self.pos))
            elif self.pos < 0:
                self.cover(bar.close_price * 1.01, abs(self.pos))

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
