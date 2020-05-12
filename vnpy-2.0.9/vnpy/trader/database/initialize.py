""""""
from .database import BaseDatabaseManager, Driver


def init(settings: dict) -> BaseDatabaseManager:
    driver = Driver(settings["driver"])
    # 这个地方传入driver，用来区分启动的是哪个数据库
    if driver is Driver.MONGODB:
        return init_nosql(driver=driver, settings=settings)
    else:
        return init_sql(driver=driver, settings=settings)
    # 这个是怎么读取到.vntrader/vt_setting.json中的数据库配置信息

def init_sql(driver: Driver, settings: dict):
    from .database_sql import init
    keys = {'database', "host", "port", "user", "password"}
    settings = {k: v for k, v in settings.items() if k in keys}
    _database_manager = init(driver, settings)
    return _database_manager


def init_nosql(driver: Driver, settings: dict):
    from .database_mongo import init
    _database_manager = init(driver, settings=settings)
    return _database_manager
