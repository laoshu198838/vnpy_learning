import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vnpy.trader.database.database import BaseDatabaseManager

if "VNPY_TESTING" not in os.environ:
    from vnpy.trader.setting import get_settings
    from .initialize import init

    settings = get_settings("database.")
    database_manager: "BaseDatabaseManager" = init(settings=settings)
    # 这里的database_manager，是在database内部代码中定义的，并会基于GlobalSetting中的数据库配置自行创建配置不同的对象，init函数就是返回这个对象