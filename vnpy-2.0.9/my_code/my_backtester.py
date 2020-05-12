import seaborn as sns
sns.set()
from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.app.cta_strategy.strategies.atr_rsi_strategy import (
    AtrRsiStrategy,
)
from datetime import datetime
# import pytest
engine = BacktestingEngine()
engine.set_parameters(
        vt_symbol="IF88.CFFEX",
        interval="1m",
        start=datetime(2018, 4, 30),
        end=datetime(2018, 12, 30),
        rate=0.3/10000,
        slippage=0.2,
        size=300,
        pricetick=0.3,
        capital=1_000_000,
    )

engine.add_strategy(AtrRsiStrategy, {})
# setting里面拥有的参数有些事从set_parameters里面进行进行选取的，但是就是不知道哪些参数是必须传的，哪些是不需要传的。
engine.load_data("mysql")
engine.run_backtesting()
engine.calculate_result()
engine.calculate_statistics()
engine.show_chart()


