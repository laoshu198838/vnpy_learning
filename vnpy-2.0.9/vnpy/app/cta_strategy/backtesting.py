from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Callable
from itertools import product
from functools import lru_cache
from time import time
import multiprocessing
import random

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pandas import DataFrame
from deap import creator, base, tools, algorithms

from vnpy.trader.constant import (Direction, Offset, Exchange,
                                  Interval, Status)
from vnpy.trader.database import database_manager
from vnpy.trader.object import OrderData, TradeData, BarData, TickData
from vnpy.trader.utility import round_to


from .base import (
    BacktestingMode,
    EngineType,
    STOPORDER_PREFIX,
    StopOrder,
    StopOrderStatus,
    INTERVAL_DELTA_MAP
)
from .template import CtaTemplate

sns.set_style("whitegrid")
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)


class OptimizationSetting:
    """
    Setting for runnning optimization.
    """

    def __init__(self):
        """"""
        self.params = {}
        self.target_name = ""

    def add_parameter(
        self, name: str, start: float, end: float = None, step: float = None
    ):
        """"""
        if not end and not step:
            self.params[name] = [start]
            return

        if start >= end:
            print("参数优化起始点必须小于终止点")
            return

        if step <= 0:
            print("参数优化步进必须大于0")
            return

        value = start
        value_list = []

        while value <= end:
            value_list.append(value)
            value += step

        self.params[name] = value_list

    def set_target(self, target_name: str):
        """"""
        self.target_name = target_name

    def generate_setting(self):
        """"""
        keys = self.params.keys()
        values = self.params.values()
        products = list(product(*values))

        settings = []
        for p in products:
            setting = dict(zip(keys, p))
            settings.append(setting)

        return settings

    def generate_setting_ga(self):
        """"""
        settings_ga = []
        settings = self.generate_setting()
        for d in settings:
            param = [tuple(i) for i in d.items()]
            settings_ga.append(param)
        return settings_ga


class BacktestingEngine:
    """
    BacktestingEngine这个是回测引擎
    """

    engine_type = EngineType.BACKTESTING
    # 这个是Enum类，枚举类，但是不知道他在这个地方用这个有什么特殊意义
    # EngineType.BACKTESTING="回测"
    gateway_name = "BACKTESTING"

    def __init__(self):
        """"""
        self.vt_symbol = ""
        # 代码和交易所，如00006.SZ
        self.symbol = ""
        # 仅仅只是代码
        self.exchange = None
        # 交易所
        self.start = None
        # 回测开始时间
        self.end = None
        # 回测结束时间
        self.rate = 0
        # 佣金费率
        self.slippage = 0
        # 滑点：理想成交价格和现实成交价格之间的差异
        self.size = 1
        self.pricetick = 0
        self.capital = 1_000_000
        # 交易资本
        self.mode = BacktestingMode.BAR
        # 也是一个枚举类，默认为BAR模式回测，表示使用的最初数据的类型bar或tick
        self.inverse = False

        self.strategy_class = None
        self.strategy = None
        self.tick: TickData
        self.bar: BarData
        self.datetime = None
        # Bar或tick的相关数据时间

        self.interval = None
        # 回测级别
        self.days = 0
        # 初始化需要的数据时间
        self.callback = None
        self.history_data = []

        self.stop_order_count = 0
        self.stop_orders = {}
        self.active_stop_orders = {}

        self.limit_order_count = 0
        # 成交的限价单信息
        self.limit_orders = {}
        # 成交了的限价单
        self.active_limit_orders = {}
        # 发出的现价单信息

        self.trade_count = 0
        # 交易的笔数
        self.trades = {}
        # 交易的相关数据

        self.logs = []
        # 日志相关数据

        self.daily_results = {}
        # 每日交易结束后最终的状态
        self.daily_df = None
        # df形式的每日状态数据

    def clear_data(self):
        """
        Clear all data of last backtesting.
        """
        self.strategy = None
        self.tick = None
        self.bar = None
        self.datetime = None

        self.stop_order_count = 0
        self.stop_orders.clear()
        self.active_stop_orders.clear()

        self.limit_order_count = 0
        self.limit_orders.clear()
        self.active_limit_orders.clear()

        self.trade_count = 0
        self.trades.clear()

        self.logs.clear()
        self.daily_results.clear()

    def set_parameters(
        self,
        vt_symbol: str,
        interval: Interval,
        start: datetime,
        rate: float,
        slippage: float,
        size: float,
        pricetick: float,
        capital: int = 0,
        end: datetime = None,
        mode: BacktestingMode = BacktestingMode.BAR,
        inverse: bool = False
    ):
        """
        回测需要的固定参数
        vt_symbol表示交易品种如IF88.CFFEX
        pricetick
        """
        self.mode = mode
        self.vt_symbol = vt_symbol
        self.interval = Interval(interval)
        # 这个地方很有可能转化为Interval.MINUTE
        # tick和bar的数据级别主要用在取数的
        self.rate = rate
        self.slippage = slippage
        self.size = size
        self.pricetick = pricetick
        self.start = start

        self.symbol, exchange_str = self.vt_symbol.split(".")
        # vt_symbol='IF88.CFFEX'这个是我们填写的交易品种代码和交易所编号
        self.exchange = Exchange(exchange_str)
        # 这里输出的是Exchange.
        self.capital = capital
        self.end = end
        self.mode = mode
        # 默认是Bar
        self.inverse = inverse
        # 不知道这个是什么

    def add_strategy(self, strategy_class: type, setting: dict):
        """
        setting表示这个策略对应的参数
        """
        self.strategy_class = strategy_class
        # 这个就是我们自己写的策略名字，这个__name__有什么奇特之处
        self.strategy = strategy_class(
            self, strategy_class.__name__, self.vt_symbol, setting
        )
        # 从这个地方开始，self.strategy就表示具体策略
        # 这个括号里面是CtaTemplate本身，class表示策略的名字，vt_symbol交易的合约代码
        # setting是一个字典，表示参数，传进去之后会在template里面抵用update_setting把里面的参数设置到我们策略对应的参数上面去
        # 这个strategy_class就相当于把我们自己写的策略加载进去

    # 这个函数就是把我们需要的数据从硬盘上面读取到内存，便于我们后期处理
    def load_data(self):
        """

        """
        self.output("开始加载历史数据")
        # 传参数的时候可以先不传，在这个地方可以设置
        if not self.end:
            self.end = datetime.now()

        if self.start >= self.end:
            self.output("起始日期必须小于结束日期")
            return

        self.history_data.clear()
        # Clear previously loaded history data
        # Load 30 days of data each time and allow for progress update
        progress_delta = timedelta(days=30)
        total_delta = self.end - self.start
        interval_delta = INTERVAL_DELTA_MAP[self.interval]
        # Interval.MiNUTE,INTERVAL_DELTA_MAP是一个字典
        #
        """{Interval.MINUTE: timedelta(minutes=1),
            Interval.HOUR: timedelta(hours=1),
            Interval.DAILY: timedelta(days=1),
        }  
        """
        # 输出 timedelta(minutes=1)
        start = self.start
        end = self.start + progress_delta
        progress = 0

        while start < self.end:
            end = min(end, self.end)
            # Make sure end time stays within set range

            if self.mode == BacktestingMode.BAR:
                data = load_bar_data(
                    self.symbol,
                    self.exchange,
                    self.interval,
                    start,
                    end
                )
                # vn.py核心数据库引擎，直接读取数据，函数的定义在本文件的下面
                # 此处相当于生成了很多的1分钟bar数据，在表格里面一行一行的显示
                # 可是在vnpy.trader.database下面没有找到这个database_manager，只在init.py找到下面这句：database_manager: "BaseDatabaseManager" = init(settings=settings)，据官方的说法：这里的database_manager，是在database内部代码中定义的，并会基于GlobalSetting中的数据库配置自行创建配置不同的对象，inti函数就是返回这个对象
            else:
                data = load_tick_data(
                    self.symbol,
                    self.exchange,
                    start,
                    end
                )

            self.history_data.extend(data)
            # 这个用于存储用于回测的数据
            # BarData(gateway_name='DB', symbol='000001', exchange=<Exchange.SZ: 'SZ'>, datetime=Timestamp('1998-05-08 00:00:00'), interval=<Interval.MINUTE: '1m'>, volume=72819.0, open_interest=20.41, open_price=20.4, high_price=20.64, low_price=20.37, close_price=20.55),
            progress += progress_delta / total_delta
            progress = min(progress, 1)
            progress_bar = "#" * int(progress * 10)
            self.output(f"加载进度：{progress_bar} [{progress:.0%}]")

            start = end + interval_delta
            # 这个地方一定要注意是从end的下一秒或一小时开始，所以需要加一个interval_delta
            end += (progress_delta + interval_delta)
            # start和end进行变化

        self.output(f"历史数据加载完成，数据量：{len(self.history_data)}")

    def run_backtesting(self):
        """"""
        if self.mode == BacktestingMode.BAR:
            func = self.new_bar
        # 这个self.mode是在加载回测引擎时，默认的BAR参数
        else:
            func = self.new_tick
        print(1)
        self.strategy.on_init()
        # 第一设置了买卖点，第二加载了初始化需要的天数，第三把回调函数callback加载进去。
        # 启动你所使用的策略的初始化,初始化里面加载了历史bar数
        # 据用于回测。而且里面已经确定了只传了10天的数据
        # Use the first [days] of history data for initializing strategy
        print(2)
        day_count = 0
        ix = 0
        # ix主要用于定位回测数据的起点，day_count主要用于和on_init里面传入的天数进行比较，已确定什么时候初始化完成。
        # 这个在做的是策略的初始化，满足天数之后就会退出
        for ix, data in enumerate(self.history_data):
            # history_data是从load_data中来的
            if self.datetime and data.datetime.day != self.datetime.day:
                day_count += 1
                if day_count >= self.days:
                    break
                # 这个self.days是load_bar中的10天，这个地方的主要目的是初始化期初需要的10天数据

            self.datetime = data.datetime
            # 这个主要是用来更新最新的时间

            self.callback(data)
            # 这一步的目的其实是往update_bar里面传输数据，直到达到规定的天数和size=100
            # 这个在具体的策略如atr_rsi_strategy中的load_bar里面，其中load_bar在ctatemplate里面，不是backtesting中的load_bar
            # 在template里面加载了callback函数，callback=on_bar，具体策略里面写了on_bar的具体方法，把bar数据推送到on_bar里面去，
            # 如果你使用的是几分钟的 on_min_bar，主要看你的策略是基于几分钟k线策略。
        self.strategy.inited = True
        # //TODO:inited=True是如何与on_bar联系起来的呢
        # 这个代码的最早出处是CtaTemplate，这个是自己写的策略继承CtaTemplate的方法产生的函数，这个表示自己写的策略如atr_rsi这些策略初始化完成
        # //TODO:这个是怎么让template检测到inited=True

        # 通过@virtual自动监测inited的状态
        self.output("策略初始化完成")

        self.strategy.on_start()
        # 对应策略的on_start函数，感觉没做什么事情
        self.strategy.trading = True
        # 这个变为True，会启动template中的send_order
        # //TODO:同理这个是怎么检测到的
        # 这个trading是也是在CtaTemplate里面设置的变量，跟inited一样
        self.output("开始回放历史数据")
        # 历史数据回放是什么意思，就是一条数据一条数据的放，就像交易所给我们一条一条数据一样。

        # Use the rest of history data for running backtesting
        # 前面的部分历史数据用于初始化，下面开始进行回测
        for data in self.history_data[ix:]:
            func(data)
        # func = self.new_bar这个是前面赋值给func的函数
        # 利用这个可以一条一条的回放
        self.output("历史数据回放结束")

    def calculate_result(self):
        """
        整体思路：先把基础数据放在类里面，然后利用类的方法计算相关的数值，算出来的值保存在类中，然后把类中的数据转化为字典，最后把字典的数据转化为DataFrame
        """
        self.output("开始计算逐日盯市盈亏")
        # 这个trades是从本文件中
        if not self.trades:
            self.output("成交记录为空，无法计算")
            return

        # Add trade data into daily reuslt.

        # ！！！这个地方的逻辑有点复杂！！！
        for trade in self.trades.values():
            # 把交易时间和交易的数据加载进入daily_result
            # self.trades是在cross_limit_price中间形成的
            d = trade.datetime.date()
            daily_result = self.daily_results[d]
            # daily_result = self.daily_results[d] = DailyResult(d, price)
            daily_result.add_trade(trade)
            # 生成的是一个self.trades的list，不要和backtesting的self.trades的字典数据搞混了
            # 把trade加入到trades里面去
            # self.daily_results[d]是在update_daily_close中创建的，然后这个函数里面会用到DailyResult(d,price)这个类。
            # self.trades的格式是{trade.vt_tradeid:trade}
            # Calculate daily result by iteration。
        # Calculate daily result by iteration。
        pre_close = 0
        start_pos = 0
        # 把数据转化为dataframe格式,为什么daily_result被处理了3次！！
        for daily_result in self.daily_results.values():
            # 这些values都是DailyResult(d,price)这个类
            daily_result.calculate_pnl(
                pre_close,
                start_pos,
                self.size,
                self.rate,
                self.slippage,
                self.inverse
            )

            pre_close = daily_result.close_price
            start_pos = daily_result.end_pos

        # Generate dataframe
        results = defaultdict(list)

        for daily_result in self.daily_results.values():
            for key, value in daily_result.__dict__.items():
                results[key].append(value)

        # 剔除其中的一些空的数据行
        self.daily_df = DataFrame.from_dict(results).set_index("date")

        self.output("逐日盯市盈亏计算完成")
        return self.daily_df

    def calculate_statistics(self, df: DataFrame = None, output=True):
        """"""
        self.output("开始计算策略统计指标")

        # Check DataFrame input exterior
        if df is None:
            df = self.daily_df

        # Check for init DataFrame
        if df is None:
            # Set all self.statistics to 0 if no trade.
            start_date = ""
            end_date = ""
            total_days = 0
            profit_days = 0
            loss_days = 0
            end_balance = 0
            max_drawdown = 0
            max_ddpercent = 0
            max_drawdown_duration = 0
            total_net_pnl = 0
            daily_net_pnl = 0
            total_commission = 0
            daily_commission = 0
            total_slippage = 0
            daily_slippage = 0
            total_turnover = 0
            daily_turnover = 0
            total_trade_count = 0
            daily_trade_count = 0
            total_return = 0
            annual_return = 0
            daily_return = 0
            return_std = 0
            sharpe_ratio = 0
            return_drawdown_ratio = 0
        else:
            # Calculate balance related time series data
            df["balance"] = df["net_pnl"].cumsum() + self.capital
            df["return"] = np.log(
                df["balance"] / df["balance"].shift(1)).fillna(0)
            df["highlevel"] = (
                df["balance"].rolling(
                    min_periods=1, window=len(df), center=False).max()
            )
            df["drawdown"] = df["balance"] - df["highlevel"]
            df["ddpercent"] = df["drawdown"] / df["highlevel"] * 100

            # Calculate self.statistics value
            start_date = df.index[0]
            end_date = df.index[-1]

            total_days = len(df)
            profit_days = len(df[df["net_pnl"] > 0])
            loss_days = len(df[df["net_pnl"] < 0])

            end_balance = df["balance"].iloc[-1]
            max_drawdown = df["drawdown"].min()
            max_ddpercent = df["ddpercent"].min()
            max_drawdown_end = df["drawdown"].idxmin()
            max_drawdown_start = df["balance"][:max_drawdown_end].argmax()
            max_drawdown_duration = (
                max_drawdown_end - max_drawdown_start).days

            total_net_pnl = df["net_pnl"].sum()
            daily_net_pnl = total_net_pnl / total_days

            total_commission = df["commission"].sum()
            daily_commission = total_commission / total_days

            total_slippage = df["slippage"].sum()
            daily_slippage = total_slippage / total_days

            total_turnover = df["turnover"].sum()
            daily_turnover = total_turnover / total_days

            total_trade_count = df["trade_count"].sum()
            daily_trade_count = total_trade_count / total_days

            total_return = (end_balance / self.capital - 1) * 100
            annual_return = total_return / total_days * 240
            daily_return = df["return"].mean() * 100
            return_std = df["return"].std() * 100

            if return_std:
                sharpe_ratio = daily_return / return_std * np.sqrt(240)
            else:
                sharpe_ratio = 0

            return_drawdown_ratio = -total_return / max_ddpercent

        # Output
        if output:
            self.output("-" * 30)
            self.output(f"首个交易日：\t{start_date}")
            self.output(f"最后交易日：\t{end_date}")

            self.output(f"总交易日：\t{total_days}")
            self.output(f"盈利交易日：\t{profit_days}")
            self.output(f"亏损交易日：\t{loss_days}")

            self.output(f"起始资金：\t{self.capital:,.2f}")
            self.output(f"结束资金：\t{end_balance:,.2f}")

            self.output(f"总收益率：\t{total_return:,.2f}%")
            self.output(f"年化收益：\t{annual_return:,.2f}%")
            self.output(f"最大回撤: \t{max_drawdown:,.2f}")
            self.output(f"百分比最大回撤: {max_ddpercent:,.2f}%")
            self.output(f"最长回撤天数: \t{max_drawdown_duration}")

            self.output(f"总盈亏：\t{total_net_pnl:,.2f}")
            self.output(f"总手续费：\t{total_commission:,.2f}")
            self.output(f"总滑点：\t{total_slippage:,.2f}")
            self.output(f"总成交金额：\t{total_turnover:,.2f}")
            self.output(f"总成交笔数：\t{total_trade_count}")

            self.output(f"日均盈亏：\t{daily_net_pnl:,.2f}")
            self.output(f"日均手续费：\t{daily_commission:,.2f}")
            self.output(f"日均滑点：\t{daily_slippage:,.2f}")
            self.output(f"日均成交金额：\t{daily_turnover:,.2f}")
            self.output(f"日均成交笔数：\t{daily_trade_count}")

            self.output(f"日均收益率：\t{daily_return:,.2f}%")
            self.output(f"收益标准差：\t{return_std:,.2f}%")
            self.output(f"Sharpe Ratio：\t{sharpe_ratio:,.2f}")
            self.output(f"收益回撤比：\t{return_drawdown_ratio:,.2f}")

        self.statistics = {
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days,
            "profit_days": profit_days,
            "loss_days": loss_days,
            "capital": self.capital,
            "end_balance": end_balance,
            "max_drawdown": max_drawdown,
            "max_ddpercent": max_ddpercent,
            "max_drawdown_duration": max_drawdown_duration,
            "total_net_pnl": total_net_pnl,
            "daily_net_pnl": daily_net_pnl,
            "total_commission": total_commission,
            "daily_commission": daily_commission,
            "total_slippage": total_slippage,
            "daily_slippage": daily_slippage,
            "total_turnover": total_turnover,
            "daily_turnover": daily_turnover,
            "total_trade_count": total_trade_count,
            "daily_trade_count": daily_trade_count,
            "total_return": total_return,
            "annual_return": annual_return,
            "daily_return": daily_return,
            "return_std": return_std,
            "sharpe_ratio": sharpe_ratio,
            "return_drawdown_ratio": return_drawdown_ratio,
        }

        return self.statistics

    def show_chart(self, df: DataFrame = None):
        """"""
        # Check DataFrame input exterior
        if df is None:
            df = self.daily_df

        # Check for init DataFrame
        if df is None:
            return

        plt.figure(figsize=(10, 16))

        balance_plot = plt.subplot(4, 1, 1)
        balance_plot.set_title("Balance")
        df["balance"].plot(legend=True)

        drawdown_plot = plt.subplot(4, 1, 2)
        drawdown_plot.set_title("Drawdown")
        drawdown_plot.fill_between(range(len(df)), df["drawdown"].values)

        pnl_plot = plt.subplot(4, 1, 3)
        pnl_plot.set_title("Daily Pnl")
        df["net_pnl"].plot(kind="bar", legend=False, grid=False, xticks=[])

        distribution_plot = plt.subplot(4, 1, 4)
        distribution_plot.set_title("Daily Pnl Distribution")
        df["net_pnl"].hist(bins=50)

        plt.show()

    def run_optimization(self, optimization_setting: OptimizationSetting, output=True):
        """"""
        # Get optimization setting and target
        settings = optimization_setting.generate_setting()
        target_name = optimization_setting.target_name

        if not settings:
            self.output("优化参数组合为空，请检查")
            return

        if not target_name:
            self.output("优化目标未设置，请检查")
            return

        # Use multiprocessing pool for running backtesting with different setting
        pool = multiprocessing.Pool(multiprocessing.cpu_count())

        results = []
        for setting in settings:
            result = (pool.apply_async(optimize, (
                target_name,
                self.strategy_class,
                setting,
                self.vt_symbol,
                self.interval,
                self.start,
                self.rate,
                self.slippage,
                self.size,
                self.pricetick,
                self.capital,
                self.end,
                self.mode,
                self.inverse
            )))
            results.append(result)

        pool.close()
        pool.join()

        # Sort results and output
        result_values = [result.get() for result in results]
        result_values.sort(reverse=True, key=lambda result: result[1])

        if output:
            for value in result_values:
                msg = f"参数：{value[0]}, 目标：{value[1]}"
                self.output(msg)

        return result_values

    def run_ga_optimization(self, optimization_setting: OptimizationSetting, population_size=100, ngen_size=30, output=True):
        """"""
        # Get optimization setting and target
        settings = optimization_setting.generate_setting_ga()
        target_name = optimization_setting.target_name

        if not settings:
            self.output("优化参数组合为空，请检查")
            return

        if not target_name:
            self.output("优化目标未设置，请检查")
            return

        # Define parameter generation function
        def generate_parameter():
            """"""
            return random.choice(settings)

        def mutate_individual(individual, indpb):
            """"""
            size = len(individual)
            paramlist = generate_parameter()
            for i in range(size):
                if random.random() < indpb:
                    individual[i] = paramlist[i]
            return individual,

        # Create ga object function
        global ga_target_name
        global ga_strategy_class
        global ga_setting
        global ga_vt_symbol
        global ga_interval
        global ga_start
        global ga_rate
        global ga_slippage
        global ga_size
        global ga_pricetick
        global ga_capital
        global ga_end
        global ga_mode
        global ga_inverse

        ga_target_name = target_name
        ga_strategy_class = self.strategy_class
        ga_setting = settings[0]
        ga_vt_symbol = self.vt_symbol
        ga_interval = self.interval
        ga_start = self.start
        ga_rate = self.rate
        ga_slippage = self.slippage
        ga_size = self.size
        ga_pricetick = self.pricetick
        ga_capital = self.capital
        ga_end = self.end
        ga_mode = self.mode
        ga_inverse = self.inverse

        # Set up genetic algorithem
        toolbox = base.Toolbox()
        toolbox.register("individual", tools.initIterate,
                         creator.Individual, generate_parameter)
        toolbox.register("population", tools.initRepeat,
                         list, toolbox.individual)
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", mutate_individual, indpb=1)
        toolbox.register("evaluate", ga_optimize)
        toolbox.register("select", tools.selNSGA2)

        total_size = len(settings)
        # number of individuals in each generation
        pop_size = population_size
        # number of children to produce at each generation
        lambda_ = pop_size
        # number of individuals to select for the next generation
        mu = int(pop_size * 0.8)

        cxpb = 0.95         # probability that an offspring is produced by crossover
        mutpb = 1 - cxpb    # probability that an offspring is produced by mutation
        ngen = ngen_size    # number of generation

        pop = toolbox.population(pop_size)
        hof = tools.ParetoFront()               # end result of pareto front

        stats = tools.self.Statistics(lambda ind: ind.fitness.values)
        np.set_printoptions(suppress=True)
        stats.register("mean", np.mean, axis=0)
        stats.register("std", np.std, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)

        # Multiprocessing is not supported yet.
        # pool = multiprocessing.Pool(multiprocessing.cpu_count())
        # toolbox.register("map", pool.map)

        # Run ga optimization
        self.output(f"参数优化空间：{total_size}")
        self.output(f"每代族群总数：{pop_size}")
        self.output(f"优良筛选个数：{mu}")
        self.output(f"迭代次数：{ngen}")
        self.output(f"交叉概率：{cxpb:.0%}")
        self.output(f"突变概率：{mutpb:.0%}")

        start = time()

        algorithms.eaMuPlusLambda(
            pop,
            toolbox,
            mu,
            lambda_,
            cxpb,
            mutpb,
            ngen,
            stats,
            halloffame=hof
        )

        end = time()
        cost = int((end - start))

        self.output(f"遗传算法优化完成，耗时{cost}秒")

        # Return result list
        results = []

        for parameter_values in hof:
            setting = dict(parameter_values)
            target_value = ga_optimize(parameter_values)[0]
            results.append((setting, target_value, {}))

        return results

    def update_daily_close(self, price: float):
        """更新每日收盘价"""
        d = self.datetime.date()

        daily_result = self.daily_results.get(d, None)
        if daily_result:
            daily_result.close_price = price
        else:
            self.daily_results[d] = DailyResult(d, price)
        #  这个DailyResult（d,price)是一个类，这个地方是不是在实例化

    def new_bar(self, bar: BarData):
        """"""
        self.bar = bar
        # 这个缓存有什么用呢，这个地方就是为了能够把bar的数据保存到实例self.bar变量中，能够被函数外部调用
        self.datetime = bar.datetime
        # 缓存T时刻最新数据K线和时间戳
        self.cross_limit_order()
        #
        self.cross_stop_order()
        # 这个在什么时候用呢，在backtesting里面没看到用止损单
        self.strategy.on_bar(bar)
        # 撮合T-1时刻的委托：限价单和停止单；策略受到委托和成交推送
        # 推送T时刻K线给策略，策略收到行情推送,具体的策略就是在on_bar里面
        # on_bar--buy--send_order--self.cta_engine.send_order--self.send_stop_order or self.send_limit_order

        self.update_daily_close(bar.close_price)
        # 更新每日收盘价

    def new_tick(self, tick: TickData):
        """"""
        self.tick = tick
        self.datetime = tick.datetime

        self.cross_limit_order()
        self.cross_stop_order()
        self.strategy.on_tick(tick)

        self.update_daily_close(tick.last_price)

    # 这个程序主要是在send_order后，当下一个订单发送过来的时候，用来判断是否成交，
    def cross_limit_order(self):
        """
        Cross limit order with last bar/tick data.
        此处的回测只用了bar进行了回测，没有用tick进行相应的回测
        次函数的作用就是在T时刻，把T-1时刻之前所有的委托都进行一遍撮合
        """
        if self.mode == BacktestingMode.BAR:
            long_cross_price = self.bar.low_price
            short_cross_price = self.bar.high_price
            long_best_price = self.bar.open_price
            short_best_price = self.bar.open_price
        else:
            long_cross_price = self.tick.ask_price_1
            short_cross_price = self.tick.bid_price_1
            long_best_price = long_cross_price
            short_best_price = short_cross_price
        """long_cross_price表示多头可能成交价格"""
        # long_best_price多头有机会最好的成交价格
        for order in list(self.active_limit_orders.values()):
            # 如果list是空的，不会进入到循环里面来，也不会报错
            # come from backtesting.send_stop_order
            # Push order update with status "not traded" (pending).key是委托号，value是委托对象
            # 此处的order是一个类
            if order.status == Status.SUBMITTING:
                order.status = Status.NOTTRADED
                self.strategy.on_order(order)
                # 这个on_order是当状态有更新的时候推送给策略，需要自己去定义
            # //TODO:很有可能order里面还有很多的列，其中一个是status
            # status这个属性是从哪来的，很可能跟object中的BaseData有关系
            # Check whether limit orders can be filled.
            long_cross = (
                order.direction == Direction.LONG
                and order.price >= long_cross_price
                and long_cross_price > 0
            )

            short_cross = (
                order.direction == Direction.SHORT
                and order.price <= short_cross_price
                and short_cross_price > 0
            )

            if not long_cross and not short_cross:
                continue
            # 这个if continue是过滤掉没有成交的单子

            # Push order udpate with status "all traded" (filled).
            order.traded = order.volume
            # 表示已经完成的成交数量
            order.status = Status.ALLTRADED
            # 变更状态
            self.strategy.on_order(order)
            # 订单的状态发生变化后，把订单发给策略
            self.active_limit_orders.pop(order.vt_orderid)
            # Push trade update
            self.trade_count += 1
            # 这个是在init中定义的变量

            if long_cross:
                trade_price = min(order.price, long_best_price)
                pos_change = order.volume
            else:
                trade_price = max(order.price, short_best_price)
                pos_change = -order.volume
            if self.trade_count != 0:
                trade = TradeData(
                    symbol=order.symbol,
                    exchange=order.exchange,
                    orderid=order.orderid,
                    tradeid=str(self.trade_count),
                    direction=order.direction,
                    offset=order.offset,
                    price=trade_price,
                    volume=order.volume,
                    time=self.datetime.strftime("%Y:%m:%d %H:%M:%S"),
                    gateway_name=self.gateway_name,
                )
                trade.datetime = self.datetime
                # 这个self.datetime是在传bar数据的时候确定的日期，为什么这个交易时间不直接放进去
                self.strategy.pos += pos_change
                # pos是外部引擎处理的
                self.strategy.on_trade(trade)
                # 把这笔交易推送出去交易

                self.trades[trade.vt_tradeid] = trade
            # trades是一个字典，保存成交的信息，trade是值

    def cross_stop_order(self):
        """
        Cross stop order with last bar/tick data.
        T时刻内，价格上下波动，形成T日K线；
        T时刻走完，基于T日以及之前数据计算通道上下轨
        T+1时刻开盘，基于上一步的通道上下轨挂出对应的停止单
        T+1时刻内，价格突破通道是触发停止单，立即发出市价单成交
        """
        if self.mode == BacktestingMode.BAR:
            long_cross_price = self.bar.high_price
            short_cross_price = self.bar.low_price
            long_best_price = self.bar.open_price
            short_best_price = self.bar.open_price
        else:
            long_cross_price = self.tick.last_price
            short_cross_price = self.tick.last_price
            long_best_price = long_cross_price
            short_best_price = short_cross_price

        for stop_order in list(self.active_stop_orders.values()):
            # Check whether stop order can be triggered.
            # self.active_stop_orders.values里面的数据结构是一个类，这里面使用类来保存数据。
            long_cross = (
                stop_order.direction == Direction.LONG
                and stop_order.price <= long_cross_price
            )

            short_cross = (
                stop_order.direction == Direction.SHORT
                and stop_order.price >= short_cross_price
            )

            if not long_cross and not short_cross:
                continue

            # Create order data.
            # 停止单最后还是要转化为限价单
            self.limit_order_count += 1

            order = OrderData(
                symbol=self.symbol,
                exchange=self.exchange,
                orderid=str(self.limit_order_count),
                direction=stop_order.direction,
                offset=stop_order.offset,
                price=stop_order.price,
                volume=stop_order.volume,
                status=Status.ALLTRADED,
                gateway_name=self.gateway_name,
                time=self.datetime.strftime("%H:%M:%S")
            )
            """
            symbol表示交易品种，如IF88，在最开始传入
            exchange表示交易所，在set_parameters中传入的
            self.limit_order_count表示限价单的数量
            stop_order表示在发送停止单时的一些信息
            stop_order.direction的方向在上面
            offset表示开或平
            status: Status = Status.SUBMITTING这个是默认值，
            getway_name是在BacktestingEngine中确定的
            """
            order.datetime = self.datetime
            # 这个地方和可能是直接给这个类添加属性，这个有什么用呢，为什么不直接放进OrderData里面去，self.datetime= bar.datetime

            self.limit_orders[order.vt_orderid] = order
            # 没有把这笔交易推给策略，没有搞懂为什么，这个不是active，因为一旦发出即成交了,两种情况，一种是t时刻就已经把单子挂在交易所那边，另一种是挂在自己的系统上面只要满足条件就提交订单，并不一定需要t+1的K线形成才可以
            # Create trade data.
            if long_cross:
                trade_price = max(stop_order.price, long_best_price)
                pos_change = order.volume
            else:
                trade_price = min(stop_order.price, short_best_price)
                pos_change = -order.volume

            self.trade_count += 1

            trade = TradeData(
                symbol=order.symbol,
                exchange=order.exchange,
                orderid=order.orderid,
                tradeid=str(self.trade_count),
                direction=order.direction,
                offset=order.offset,
                price=trade_price,
                volume=order.volume,
                time=self.datetime.strftime("%H:%M:%S"),
                gateway_name=self.gateway_name,
            )
            trade.datetime = self.datetime
            # direction表示方向，offset表示经常模式，一手多两手空，会平掉多仓空仓，然后开
            # 一个空仓
            # 这个time是一个字符串
            self.trades[trade.vt_tradeid] = trade

            # Update stop order.
            stop_order.vt_orderids.append(order.vt_orderid)
            stop_order.status = StopOrderStatus.TRIGGERED

            if stop_order.stop_orderid in self.active_stop_orders:
                self.active_stop_orders.pop(stop_order.stop_orderid)

            # Push update to strategy.
            self.strategy.on_stop_order(stop_order)
            self.strategy.on_order(order)
            # 这个地方把停止单推给了策略
            self.strategy.pos += pos_change
            self.strategy.on_trade(trade)

    def load_bar(
        self,
        vt_symbol: str,
        days: int,
        interval: Interval,
        callback: Callable,
        use_database: bool
    ):
        """"""
        self.days = days
        self.callback = callback

    def load_tick(
        self,
        vt_symbol: str,
        days: int,
        callback: Callable
    ):
        """"""
        self.days = days
        self.callback = callback

    def send_order(
        self,
        strategy: CtaTemplate,
        direction: Direction,
        offset: Offset,
        price: float,
        volume: float,
        stop: bool,
        lock: bool
    ):
        """"""
        price = round_to(price, self.pricetick)
        if stop:
            vt_orderid = self.send_stop_order(direction, offset, price, volume)
        else:
            vt_orderid = self.send_limit_order(
                direction, offset, price, volume)
        return [vt_orderid]
        # 最后这个是把返回来的vt_orderid放入一个list中

    def send_stop_order(
        self,
        direction: Direction,
        offset: Offset,
        price: float,
        volume: float
    ):
        """"""
        self.stop_order_count += 1

        stop_order = StopOrder(
            vt_symbol=self.vt_symbol,
            direction=direction,
            offset=offset,
            price=price,
            volume=volume,
            stop_orderid=f"{STOPORDER_PREFIX}.{self.stop_order_count}",
            strategy_name=self.strategy.strategy_name,
        )
        # STOPORDER_PREFIX = "STOP"在base中已经定义好了
        # 不是很清楚这个stop_orderid是怎么来的
        self.active_stop_orders[stop_order.stop_orderid] = stop_order
        # 这个用于后期遍历
        self.stop_orders[stop_order.stop_orderid] = stop_order
        # 这个用于存储信息

        return stop_order.stop_orderid

    def send_limit_order(
        self,
        direction: Direction,
        offset: Offset,
        price: float,
        volume: float
    ):
        """"""
        self.limit_order_count += 1

        order = OrderData(
            symbol=self.symbol,
            exchange=self.exchange,
            orderid=str(self.limit_order_count),
            direction=direction,
            offset=offset,
            price=price,
            volume=volume,
            status=Status.SUBMITTING,
            gateway_name=self.gateway_name,
        )
        # volume是在buy里面的fixed_size
        order.datetime = self.datetime
        # 这个很可能是添加order的属性
        self.active_limit_orders[order.vt_orderid] = order
        self.limit_orders[order.vt_orderid] = order

        return order.vt_orderid



class DailyResult:
    """"""

    def __init__(self, date: date, close_price: float):
        """"""
        self.date = date
        self.close_price = close_price
        self.pre_close = 0

        self.trades = []  # 当日发生的盈亏
        self.trade_count = 0

        self.start_pos = 0
        self.end_pos = 0

        self.turnover = 0
        self.commission = 0  # 佣金
        self.slippage = 0  # 滑点

        self.trading_pnl = 0  # 当日交易盈亏
        self.holding_pnl = 0  # 今日之前仓位的盈亏
        self.total_pnl = 0  # 总的盈亏
        self.net_pnl = 0  # 净盈亏去掉佣金和滑点

    def add_trade(self, trade: TradeData):
        """"""
        self.trades.append(trade)
        # 这个trade是从BarData那里面来的
        # 不要和backtesting中的self.trades搞混了，那個是字典數據，这个是列表

    def calculate_pnl(
        self,
        pre_close: float,
        start_pos: float,
        size: int,
        rate: float,
        slippage: float,
        inverse: bool
    ):  # 在前面327和328行生成的，不断的进行迭代,run_backtesting中
        """"""
        # If no pre_close provided on the first day,
        # use value 1 to avoid zero division error
        if pre_close:
            self.pre_close = pre_close
        # 把相关数据保存到具体的实例中去
        else:
            self.pre_close = 1

        # Holding pnl is the pnl from holding position at day start
        self.start_pos = start_pos
        self.end_pos = start_pos

        if not inverse:     # For normal contract
            self.holding_pnl = self.start_pos * \
                (self.close_price - self.pre_close) * size
        else:               # For crypto currency inverse contract
            self.holding_pnl = self.start_pos * \
                (1 / self.pre_close - 1 / self.close_price) * size

        # Trading pnl is the pnl from new trade during the day
        self.trade_count = len(self.trades)

        for trade in self.trades:
            if trade.direction == Direction.LONG:
                pos_change = trade.volume
            else:
                pos_change = -trade.volume

            self.end_pos += pos_change

            # For normal contract
            if not inverse:
                turnover = trade.volume * size * trade.price
                self.trading_pnl += pos_change * \
                    (self.close_price - trade.price) * size
                self.slippage += trade.volume * size * slippage
            # For crypto currency inverse contract
            else:
                turnover = trade.volume * size / trade.price
                self.trading_pnl += pos_change * \
                    (1 / trade.price - 1 / self.close_price) * size
                self.slippage += trade.volume * \
                    size * slippage / (trade.price ** 2)

            self.turnover += turnover
            # self.turnover表示累计的成交量
            self.commission += turnover * rate
            # 每天的成交量与佣金率的乘积

        # Net pnl takes account of commission and slippage cost
        self.total_pnl = self.trading_pnl + self.holding_pnl
        # 总盈利情况
        self.net_pnl = self.total_pnl - self.commission - self.slippage
        # 净盈利情况


def optimize(
    target_name: str,
    strategy_class: CtaTemplate,
    setting: dict,
    vt_symbol: str,
    interval: Interval,
    start: datetime,
    rate: float,
    slippage: float,
    size: float,
    pricetick: float,
    capital: int,
    end: datetime,
    mode: BacktestingMode,
    inverse: bool
):
    """
    Function for running in multiprocessing.pool
    """
    engine = BacktestingEngine()

    engine.set_parameters(
        vt_symbol=vt_symbol,
        interval=interval,
        start=start,
        rate=rate,
        slippage=slippage,
        size=size,
        pricetick=pricetick,
        capital=capital,
        end=end,
        mode=mode,
        inverse=inverse
    )

    engine.add_strategy(strategy_class, setting)
    engine.load_data()
    engine.run_backtesting()
    engine.calculate_result()
    self.statistics = engine.calculate_statistics(output=False)

    target_value = self.statistics[target_name]
    return (str(setting), target_value, self.statistics)


@lru_cache(maxsize=1000000)
def _ga_optimize(parameter_values: tuple):
    """"""
    setting = dict(parameter_values)

    result = optimize(
        ga_target_name,
        ga_strategy_class,
        setting,
        ga_vt_symbol,
        ga_interval,
        ga_start,
        ga_rate,
        ga_slippage,
        ga_size,
        ga_pricetick,
        ga_capital,
        ga_end,
        ga_mode,
        ga_inverse
    )
    return (result[1],)


def ga_optimize(parameter_values: list):
    """"""
    return _ga_optimize(tuple(parameter_values))


@lru_cache(maxsize=999)
def load_bar_data(
    symbol: str,
    exchange: Exchange,
    interval: Interval,
    start: datetime,
    end: datetime
):
    """"""
    return database_manager.load_bar_data(
        symbol, exchange, interval, start, end
    )


@lru_cache(maxsize=999)
def load_tick_data(
    symbol: str,
    exchange: Exchange,
    start: datetime,
    end: datetime
):
    """"""
    return database_manager.load_tick_data(
        symbol, exchange, start, end
    )


# GA related global value
ga_end = None
ga_mode = None
ga_target_name = None
ga_strategy_class = None
ga_setting = None
ga_vt_symbol = None
ga_interval = None
ga_start = None
ga_rate = None
ga_slippage = None
ga_size = None
ga_pricetick = None
ga_capital = None
