import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vnpy.trader.database.database import BaseDatabaseManager

if "VNPY_TESTING" not in os.environ:
    # VNPY_TESTING是什么？？
    from vnpy.trader.setting import get_settings
    from .initialize import init
    # 读取setting中的参数，
    settings = get_settings("database.")
    database_manager: "BaseDatabaseManager" = init(settings=settings)
    # 这种表示方式就相当于database_manager等于冒号后面的
    # init是initialize中的init
    # 这里的database_manager，是在database内部代码中定义的，并会基于GlobalSetting中的数据库配置自行创建配置不同的对象，init函数就是返回这个对象