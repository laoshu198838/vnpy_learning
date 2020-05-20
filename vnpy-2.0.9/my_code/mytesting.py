# coding='utf-8'


"""
删除行：Ctrl+x
复制行：ctrl+shift+x
显示调试控制台：ctrl+shift+Y
资源管理器：ctrl+shift+E
搜索：ctrl+shift+F
运行和调试：ctrl+shift+D
Extension：ctrl+shift+X
设置：ctrl+，
拆分：ctrl+\
关闭窗口：ctrl+W
关闭编辑器：ctrl+F4
选择所有匹配项：ctrl+shift+L
转到括号：ctrl+shift+\
跳转到哪一行：ctrl+G
打开键盘快捷键设置页面：ctrl+1
打开新的外部终端：ctrl+shift+c
全部展开：ctrl+K,J
全部折叠：ctr+K,O
展开所有区域：ctrl+k+9
放大：ctrl+shift+=
在上面插入行：ctrl+shift+enter
注释代码块(""" """)：ctrl+shift+A
折叠所有文件夹：ctrl+shift+[]
格式化文档：alt+shift+F
 """

from pymysql import connect
from typing import List, Tuple, Dict
from pathlib import Path
from datetime import datetime, timedelta, time
import os
import random
import numpy as np
import pandas as pd
import time
from pymongo import MongoClient
from multiprocessing import Pool
from pymongo import MongoClient
import pymongo.errors as mongoerr
import matplotlib as mpl
import matplotlib.pyplot as plt
from datetime import datetime
import sys
from peewee import *

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.database import database_manager
from vnpy.trader.object import TickData
from gm.api import *
from peewee import *

import sys
from PyQt5.QtWidgets import QApplication,QWidget,QMainWindow
from Ui_first import Ui_MainWindow
import Ui_MainWinHorizontalLayout
if __name__=='__main__':
    # 创建QApplication类的实例
    app = QApplication(sys.argv)
    # 生成主窗口上
    mainWindow = QMainWindow()
    # 创建类
    ui = Ui_MainWinHorizontalLayout.Ui_MainWindow()
    # 主窗口添加控件
    ui.setupUi(mainWindow)
    mainWindow.show()
    sys.exit(app.exec_())
# 连接数据库
database = MySQLDatabase('python_test', user='root',
                         password='zlb198838', host='localhost', port=3306)
database_1 = MySQLDatabase('stock_code_db', user='root',
                         password='zlb198838', host='localhost', port=3306)
# 定义Person


class Class_4(Model):
    id = AutoField()
    symbol: str = CharField()
    exchange: str = CharField()
    datetime: datetime = DateTimeField()
    interval: str = CharField()

    volume: float = FloatField()
    open_interest: float = FloatField()
    open_price: float = FloatField()
    high_price: float = FloatField()
    low_price: float = FloatField()
    close_price: float = FloatField()

    class Meta:
        database = database
        indexes = ((("symbol", "exchange", "interval", "datetime"), True),)
        # 表示这四个连起来必须唯一！！

class User(Model):
    id = AutoField()
    username: str = CharField()
    class Meta:
        database = database
        
class Table_name(Model):
    id = AutoField()
    # symbol: str = CharField()
    # exchange: str = CharField()
    datetime: datetime = DateTimeField()
    # interval: str = CharField()

    open_price: float = FloatField()
    high_price: float = FloatField()
    low_price: float = FloatField()
    close_price: float = FloatField()
    volume: float = FloatField()
    open_interest: float = FloatField()
    class Meta:
        database = database
        table_name='000004'



df_all = pd.read_csv(
    r'C:\Users\Administrator\Desktop\000001.csv',
    # parse_dates=["trade_date"],
    usecols=[2, 3, 4, 5, 6, 7],
    # index_col=0
)

df_all.datetime=df_all.trade_date.apply(lambda x:pd.to_datetime(x))(df_all.trade_date)
print(df_all.head(2))
print(df_all.types)
columns = df_all.columns
print(columns)
json_1 = df_all.to_json(orient="index")
dict_1=df_all.to_dict(orient="records")
print(dict_1)
print(json_1[0])
list_1 = [list(i) for i in df_all.iterlists()]

print(list_1[0:5])
df_part = df_all['trade_date']
df_part_2=df_all[['trade_date']]
print(df_part_2.head(5))
print(type(df_part_2))
print('===============')
print(type(df_part))
print(df_part.head(5))
print('===============')
list_1=df_part.tolist()
list_2=df_part_2.tolist()
print(list_1[0:5])
# df_all=df_all[0:5]
# tuple_data = [list(i) for i in df_all.itertuples()]
# tuple_data[0][0]=8
# print(tuple_data[0:5])
# print(df_all.head(5))
# database.connect()
# database.create_tables([Table_name])
# Table_name.insert_many(tuple_data, fields=[Table_name.id,Table_name.datetime,Table_name.open_price,Table_name.high_price,Table_name.low_price,Table_name.close_price,Table_name.volume]).execute()
u1, u2, u3 = [User.create(username='ut%s' % i) for i in (1, 2, 3)]
print(u1)
# Now we'll modify the user instances.
# u1.username = 'u1-x'
# u2.username = 'u2-y'
# u3.username = 'u3-z'

# Update all three users with a single UPDATE query.
User.bulk_update([u1, u2, u3], fields=[User.username])
list_1=[]



database.connect()
database.create_tables([Class_4])
user = User(id=3,username='Charlie')
# print(user.save())
# print(user.id)
huey = User()
# huey.username = 'Huey'
# huey.save()
print(User.insert(username='Mickey1').execute())
# p=Class_1(id=175201, symbol='IF88',name='zhoulibing',exchange='SZSE',open_interest=0)
p = Class_4(id=175201,exchange='SZSE', symbol='IF88', datetime=datetime(1990, 12, 22), interval='1m', volume=490, open_interest=0, open_price=3450, high_price=3488, low_price=3450, close_price=3450)
# p_1=Class_4.insert(exchange='SZSE', symbol='IF88', datetime=datetime(1990, 12, 21), interval='1m', volume=490, open_interest=0, open_price=3450, high_price=3488, low_price=3450, close_price=3450).execute()
p.save()
Class_4.update({'symbol':"SZSE",'interval':"d"}).execute()
# return Class_1

conn = connect(
    host='localhost',
    port=3306,
    user='root',
    password='zlb198838',
    database='stock_code_db',
    charset='utf8'
)
cs_1 = conn.cursor()
sql = "show tables"
cs_1.execute(sql)


db = MySQLDatabase("python_test", host="localhost",
                   port=3306, user="root", passwd="zlb198838")
db.connect()


class BaseModel(Model):

    class Meta:
        database = db


class User(BaseModel):
    username = CharField(unique=True)


class Tweet(BaseModel):
    user = ForeignKeyField(User, related_name='tweets')
    message = TextField()
    created_date = DateTimeField(default=datetime.now)
    is_published = BooleanField(default=True)


if __name__ == "__main__":
    # 创建表
    User.create_table()  # 创建User表
    Tweet.create_table()  # 创建Tweet表


def record_insert_date(self, stock: str, date):
    """ 
    记录每个股票插入数据的截止日期
    """
    try:
        sql_1 = f"select * from stock_insert_date_record where stock_code=`{stock}`;"
        if self.cs.execute(sql_1) == 0:
            sql_2 = f"insert into stock_insert_date_record (stock_code,datetime) values (`{stock}`,{date});"
            self.cs.execute(sql_2)
        else:
            sql_3 = f"update datetime={date} where stock_code={stock};"
            self.cs.execute(sql_3)
        self.cs.commit()
    except Exception as e:
        print(e)


df_all = pd.read_csv(
    r'C:\Users\Administrator\Desktop\000001.csv',
    # parse_dates=["trade_date"],
    usecols=[2, 3, 4, 5, 6, 10, 11],
    # index_col=0
)
print(df_all['trade_date'][0])
df_all['datetime_T'] = pd.to_datetime(df_all.trade_date, format='%Y%m%d')

df_all.drop(['datetime_T'], axis=1, inplace=True)
print(df_all)
# df_all['datetime'] = df_all.trade_date
df_all.set_index('trade_date', inplace=True, drop=False)
df_all.trade_date = pd.to_datetime(df_all.trade_date, format='%Y%m%d')
print(df_all.head(2))
print(df_all.dtypes)
my_list = [tuple(i) for i in df_all.itertuples()]
print(my_list[0])
# for row in df_all.itertuples():


sql = "insert into `000002` \
    (datetime, open_price, high_price, low_price, close_price, volume, amount) \
    values(%s, %s, %s, %s, %s, %s, %s) "

# cs_1.executemany(sql, my_list)
conn.rollback()
conn.commit()


class JD():
    def __init__(self):
        self.conn = connect(
            host='localhost',
            port=3306, user='root',
            password='zlb198838',
            database='python_test',
            charset='utf8'
        )
        self.cs_1 = self.conn.cursor()

    def close_conn(self):
        """ 关闭连接 """
        self.cs_1.close()
        self.conn.close()
        print('查询结束！')

    def execute_sql(self, sql):
        """ 执行sql查询 """
        self.cs_1.execute(sql)
        for info in self.cs_1.fetchall():
            print(info)

    def query_all_goods(self):
        """ 查询所有商品 """
        sql = 'select * from goods;'
        self.execute_sql(sql)

    def query_all_cates(self):
        """ 查询所有商品类别 """
        sql = 'select name from goods_cates;'
        self.execute_sql(sql)

    def query_all_brands(self):
        """ 查询所有品牌 """
        sql = 'select name from goods_brands;'
        self.execute_sql(sql)

    @staticmethod
    def print_info():
        """ 打印输入信息 """
        print('-----JD-----')
        print('请选择需要查询的信息')
        print('0:停止查询')
        print('1:查询所有商品信息')
        print('2:查询所有类别')
        print('3:查询所有品牌')
        return input('请输入查询信息（数字）：')

    def run(self):
        """ 运行查询 """
        while True:
            num = self.print_info()
            if num == '0':
                self.close_conn()
                break
            elif num == '1':
                self.query_all_goods()
            elif num == '2':
                self.query_all_cates()
            elif num == '3':
                self.query_all_brands()
            else:
                print('输入错误！！请输入正确数字！')


def main():
    jd = JD()
    jd.run()


if __name__ == "__main__":
    main()
