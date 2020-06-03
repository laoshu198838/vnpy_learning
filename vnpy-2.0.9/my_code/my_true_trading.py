import multiprocessing
from time import sleep
from datetime import datetime, time
from logging import INFO

from vnpy.event import EventEngine
from vnpy.trader.setting import SETTINGS
from vnpy.trader.engine import MainEngine

from vnpy.gateway.ctp import CtpGateway
from vnpy.app.cta_strategy import CtaStrategyApp
from vnpy.app.cta_strategy.base import EVENT_CTA_LOG


SETTINGS["log.active"] = True
SETTINGS["log.level"] = INFO
SETTINGS["log.console"] = True


ctp_setting = {
    "用户名": "161098",
    "密码": "zlb&198838",
    "经纪商代码": "9999",
    "交易服务器": "180.168.146.187:10100",
    "行情服务器": "180.168.146.187:10110",
    "产品名称": "simnow_client_test",
    "授权编码": "0000000000000000",
    "产品信息": "11111"
}
strategy_setting = {
    "class_name":"AtrRsiStrategy",
    "atr_length":22,
    "atr_ma_length":10,
    "rsi_length":5,
    "rsi_entry":16,
    "trailing_percent":0.8,
    "fixed_size":1,
}


def run_child():
    """
    Running in the child process.
    """
    SETTINGS["log.file"] = True

    event_engine = EventEngine()
    print(event_engine.__module__)
    # 把event和处理函数联系起来
    main_engine = MainEngine(event_engine)
    # 一个大的类来把策略、ctp行情、事件引擎和实盘引擎结合起来。
    # 把事件引擎加载进去主引擎
    main_engine.add_gateway(CtpGateway)
    # 最终是返回CtpGateway接口，把行情接口和交易接口添加进去
    cta_engine = main_engine.add_app(CtaStrategyApp)
    # 把CtaEngine这个实盘引擎加载进来，类似回测中的backtesting
    # 使用的具体策略在CTAEngine里面加载了。
    # 返回CtaEngine
    main_engine.write_log("主引擎创建成功")

    log_engine = main_engine.get_engine("log")
    event_engine.register(EVENT_CTA_LOG, log_engine.process_log_event)
    main_engine.write_log("注册日志事件监听")

    main_engine.connect(ctp_setting, "CTP")
    main_engine.write_log("连接CTP接口")
    
    sleep(1)
    
    main_engine.get_all_contracts()
    sleep(2)
    cta_engine.init_engine()
    main_engine.write_log("CTA策略初始化完成")
    
    
    cta_engine.init_strategy('AtrRsiStrategy')
    # 给策略初始化留足时间
    sleep(1)
    main_engine.write_log("CTA策略全部初始化")
    
    cta_engine.start_strategy('AtrRsiStrategy')
    main_engine.write_log("CTA策略全部启动")

    while True:
        sleep(1)


def run_parent():
    """
    Running in the parent process.
    """
    print("启动CTA策略守护父进程")

    # Chinese futures market trading period (day/night)
    DAY_START = time(8, 45)
    DAY_END = time(15, 30)

    NIGHT_START = time(20, 45)
    NIGHT_END = time(2, 45)

    child_process = None

    while True:
        current_time = datetime.now().time()
        trading = False

        # Check whether in trading period
        if (
            (current_time >= DAY_START and current_time <= DAY_END)
            or (current_time >= NIGHT_START)
            or (current_time <= NIGHT_END)
        ):
            trading = True

        # Start child process in trading period
        if trading and child_process is None:
            print("启动子进程")
            child_process = multiprocessing.Process(target=run_child)
            child_process.start()
            print("子进程启动成功")

        # 非记录时间则退出子进程
        if not trading and child_process is not None:
            print("关闭子进程")
            child_process.terminate()
            child_process.join()
            child_process = None
            print("子进程关闭成功")

        sleep(1)


if __name__ == "__main__":
    # run_parent()
    event_engine = EventEngine()
    print(event_engine.__module__)
    
