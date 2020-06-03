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


class AtrRsiStrategy(CtaTemplate):
    """"""

    author = "用Python的交易员"
    # 这些参数都是整个类可以使用的参数
    atr_length = 22
    # 计算ATR指标的窗口数
    atr_ma_length = 10
    # ATR均线的窗口数
    rsi_length = 5
    # RSI的窗口期
    rsi_entry = 16
    # rsi开仓信号
    trailing_percent = 0.8
    fixed_size = 1

    atr_value = 0
    atr_ma = 0
    rsi_value = 0
    rsi_buy = 0
    rsi_sell = 0
    intra_trade_high = 0
    intra_trade_low = 0

    parameters = ["atr_length", "atr_ma_length", "rsi_length",
                  "rsi_entry", "trailing_percent", "fixed_size"]
    variables = ["atr_value", "atr_ma", "rsi_value", "rsi_buy", "rsi_sell"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        # cta_engine是很可能就是add_strategy中self.strategy = strategy_class(self, strategy_class.__name__, self.vt_symbol, setting)中的self
        # setting如果不传内容就会使用parameters里面的参数用作策略的参数
        # 这种超类就是子类可以改写父类的方法，同时也还可以调用父类的方法，只是有先后顺序差别，这样就可以把一些函数部分共性放在父类，差异部分在自己的策略函数中写。
        self.bg = BarGenerator(self.on_bar)  # 简化书写过程
        self.am = ArrayManager()  # 同理

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")

        self.rsi_buy = 50 + self.rsi_entry  # 初始化好买点
        self.rsi_sell = 50 - self.rsi_entry  # 初始化好卖点

        # 母类template中的CtaTemplate策略中的方法，只加载十天的数据，那我们测试好几年的数据是怎么加载进去呢，这个会在后面调用回测中的load_data函数
        self.load_bar(10)
        # rsi---template----backtesting，这个调用的路径
        # 如果你使用的是其他的分钟k线，就需要在这里面传入
        # 具体流程是先调用template中的load_bar,然后template中的load_bar再调用backtesting.py中的load_bar,把回调函数和天数加载进去，方便后面加载数据。

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")  # 输出提示文字，同时还会执行write_log里面的程序

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        print(2)
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        他这个地方是怎么接收bar
        """
        self.cancel_all()
    
        am = self.am
        am.update_bar(bar)
        # 数据一旦加载到初始化需要的数量就会自动启动inited，在run_backtesting里面启动
        # update_bar 这个函数是在Arraymanager里面
        if not am.inited:
            return

        atr_array = am.atr(self.atr_length, array=True)
        self.atr_value = atr_array[-1]
        self.atr_ma = atr_array[-self.atr_ma_length:].mean()
        self.rsi_value = am.rsi(self.rsi_length)

        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            if self.atr_value > self.atr_ma:
                if self.rsi_value > self.rsi_buy:
                    self.buy(bar.close_price + 5, self.fixed_size)
                elif self.rsi_value < self.rsi_sell:
                    self.short(bar.close_price - 5, self.fixed_size)

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price
            # low没有什么用，只是用来更新最近low价格
            long_stop = self.intra_trade_high * \
                (1 - self.trailing_percent / 100)
            self.sell(long_stop, abs(self.pos), stop=True)

        elif self.pos < 0:
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            self.intra_trade_high = bar.high_price

            short_stop = self.intra_trade_low * \
                (1 + self.trailing_percent / 100)
            self.cover(short_stop, abs(self.pos), stop=True)

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


if __name__ == "__main__":
    print(AtrRsiStrategy.__name__)
