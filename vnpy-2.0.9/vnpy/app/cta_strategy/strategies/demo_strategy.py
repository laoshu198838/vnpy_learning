from typing import Any

from vnpy.app.cta_strategy import(
    CtaTemplate,
    BarGenerator,
    ArrayManager
)

class DemoStrategy(CtaTemplate):
    """"""
    author = '周利兵'
    #定义参数
    fast_window = 10
    slow_window = 20

    #定义变量
    fast_ma0 = 0.0
    fast_ma1 = 0.0
    slow_ma0 = 0.0
    slow_ma1 = 0.0

    parameters = [
        'fast_window',
        'slow_window',
    ]

    variables = [
        'fast_ma0',
        'fast_ma1',
        'slow_ma0',
        'slow_ma1',
    ]

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ):
        super().__init__(cta_engine,strategy_name,vt_symbol,setting)

        self.bg = NewBarGenerator(
            self.on_bar,
            window=7,
            on_window_bar=self.on_7min_bar,
            interval=Interval.MINUTE
        )
        self.am = ArrayManager()

    def on_init(self):
        """策略初始化"""
        self.write_log("策略初始化")

        self.load_bar(10)

    def on_start(self):
        """启动"""
        self.write_log("策略启动")

    def on_stop(self):
        """停止"""
        self.write_log("策略停止")

    def on_tick(self,tick:TickData):
        """TICK更新"""
        self.bg.update_tick(t)

    def on_7min_bar(self,bar:BarData):
        """K线更新"""
        am = self.am
    
        am.update_bar(bar)
        if am.inited:
            return

        #计算技术指标
        fast_ma = am.sma(self.fast_window,array = True)
        self.fast_ma0 = fast_ma[-1]
        self.fast_ma1 = fast_ma[-2]

        slow_ma = am.sma(self.slow_window, array=True)
        self.slow_ma0 = slow_ma[-1]
        self.slow_ma1 = slow_ma[-2]

        #判断均线定义
        cross_over = (self.fast_ma0 >= self.slow_ma0 and
                    self.fast_ma1 < self.slow_ma1)

        cross_below = (self.fast_ma0 <= self.slow_ma0 and
                       self.fast_ma1 > self.slow_ma1)

        if cross_over:
            price = bar.close_price + 5

            if not self.pos:
                self.buy(price,1)
            elif self.pos < 0:
                self.cover(price,1)
                self.buy(price,1)
        elif cross_below:
            price = bar.close_price - 5

            if not self.pos:
                self.short(price,1)
            elif self.pos > 0:
                self.sell(price,1)
                self.short(price,1)

        # 更新图形界面
        self.put_event()


class NewBarGenerator(BarGenerator):
    """"""

    def __init__(
        on_bar:callable,
        window:int = 0,
        on_window_bar:callable = None,
        interval:Interval = Interval.Minute
    ):
        super().__init__(on_bar,window,on_window_bar,interval)
    #利用55秒这个时间点去划分k先，避免过度拥挤，滑点过多。
    def update_tick(self, tick:TickData):
        """
        它是如何知道有新的tick进来的，难道是自动检测吗，如果是他是在哪个地方可以自动检测新的tick，
        然后加载进入update_tick
        Update new tick data into generator.
        tick后面的:是用来进行解释参数的,能够对tick里面的数据进行联想，方便输入
        """
        new_minute = False
        #用来判断是不是新的分钟，如果是新的分钟我们就要把之前的tick数据推送出去
        # Filter tick data with 0 last price
        if not tick.last_price:
            #过滤掉初始化的一些数据，也就是历史数据，
            # 但是不知道lastprice具体的怎么来的
            return
        
        if not self.bar:
            #这个就是用来判断是否是第一根k线,而且是新的k线刚刚#开始，还没有结束
            new_minute = True
        elif tick.datetime.second >= 50 and self.last_tick.datetime.second <50:
            #bar的数据结构是什么样的，难
            # 从下面的self.bar可以看出什么样的。
            self.bar.datetime = self.bar.datetime.replace(
                second=0, microsecond=0
            )
            self.on_bar(self.bar)#把他推送出去是什么意思，难道bar是正在处理的，on_bar是已经处理好了
                # 类似一个仓库一样

            new_minute = True

        if new_minute:#新的分钟k线形成的时候
            self.bar = BarData(
                symbol=tick.symbol,
                exchange=tick.exchange,
                interval=Interval.MINUTE,
                datetime=tick.datetime,
                gateway_name=tick.gateway_name,
                open_price=tick.last_price,
                high_price=tick.last_price,
                low_price=tick.last_price,
                close_price=tick.last_price,
                open_interest=tick.open_interest
            )
        else:#分钟k线没有形成的时候
            self.bar.high_price = max(self.bar.high_price, tick.last_price)
            self.bar.low_price = min(self.bar.low_price, tick.last_price)
            self.bar.close_price = tick.last_price
            self.bar.open_interest = tick.open_interest
            self.bar.datetime = tick.datetime

        if self.last_tick:
            volume_change = tick.volume - self.last_tick.volume
            #tick.volume表示的是截止到目前全部的成交量
            self.bar.volume += max(volume_change, 0)

        self.last_tick = tick#这个tick是一条一条推送的吗，要不然有几行怎么知道选哪行呢

    def update_bar(self, bar: BarData):
        """
        Update 1 minute bar into generator
        """
        # If not inited, creaate window bar object
        if not self.window_bar:
            # Generate timestamp for bar data
            if self.interval == Interval.MINUTE:
                dt = bar.datetime.replace(second=0, microsecond=0)
            else:
                dt = bar.datetime.replace(minute=0, second=0, microsecond=0)

            self.window_bar = BarData(
                symbol=bar.symbol,
                exchange=bar.exchange,
                datetime=dt,
                gateway_name=bar.gateway_name,
                open_price=bar.open_price,
                high_price=bar.high_price,
                low_price=bar.low_price
            )
        # Otherwise, update high/low price into window bar
        else:
            self.window_bar.high_price = max(
                self.window_bar.high_price, bar.high_price)
            self.window_bar.low_price = min(
                self.window_bar.low_price, bar.low_price)

        # Update close price/volume into window bar
        self.window_bar.close_price = bar.close_price
        self.window_bar.volume += int(bar.volume)
        self.window_bar.open_interest = bar.open_interest

        # Check if window bar completed
        finished = False

        if self.interval == Interval.MINUTE:
            # x-minute bar
            # if not (bar.datetime.minute + 1) % self.window:
            #     finished = True
            if self.last_bar and bar.datetime.minute != self.last_bar.datetime.minute:
                self.interval_count += 1

                if not self.interval_count % self.window:
                    finished =True
                    self.interval_count = 0

        elif self.interval == Interval.HOUR:
            if self.last_bar and bar.datetime.hour != self.last_bar.datetime.hour:
                # 1-hour bar
                if self.window == 1:
                    finished = True
                # x-hour bar
                else:
                    self.interval_count += 1

                    if not self.interval_count % self.window:
                        finished = True
                        self.interval_count = 0

        if finished:
            self.on_window_bar(self.window_bar)
            self.window_bar = None

        # Cache last bar object
        self.last_bar = bar
        
         

