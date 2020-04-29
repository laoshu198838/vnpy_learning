from vnpy.app.cta_strategy.csv_backtesting import CsvBacktestingEngine, OptimizationSetting
from vnpy.app.cta_strategy.base import BacktestingMode
from vnpy.app.cta_strategy.strategies.atr_rsi_strategy import (
    AtrRsiStrategy,
)
from datetime import datetime
import os
# 加载Csv引擎
engine = CsvBacktestingEngine()
# 加载策略
engine.add_strategy(AtrRsiStrategy, {})

# 存储股票数据的地址
path = 'D:\\The Road For Finacial Statics\\Python\\02.Learning Materrials\\02.Data\\02.daily_BarData'

# 获取股票代码和相对应的股票文件名称
stock_code_list, filename_list = engine.get_filename(path)

# 对所有的股票进行回测
for ix, filename in enumerate(filename_list):

    print('('+str(engine.rb_count+1)+').'+stock_code_list[ix][:-3] + '回测开始')
    
    if ix > 1:
        break
    
    engine.set_parameters(
        vt_symbol=stock_code_list[ix],
        interval="d",
        start=datetime(1998, 4, 1),
        end=datetime(2020, 5, 10),
        rate=0.3 / 10000,
        slippage=0.2,
        size=300,
        pricetick=0.2,
        capital=1_000_000,
    )
    try:
        engine.load_data(filename)
        engine.run_backtesting()
        engine.calculate_result()
        engine.calculate_statistics(output=False)
        engine.save_all_statistics(stock_code_list[ix][:-3])
    except:
        print(stock_code_list[ix][:-3] + ':回测报错！')
        continue
    
    # 清空缓存数据，准备下一个股票的回测
    engine.clear_data()
    print('('+str(engine.rb_count)+').'+stock_code_list[ix][:-3] + '回测结束')

engine.to_csv('C:\\Users\\Administrator\\Desktop')
print(str(engine.rb_count)+'个股票，全部回测结束！！')
# engine.show_all_stock_chart()
