# coding='utf-8'


"""
复制行：ctrl+shift+x
显示调试控制台：ctrl+shift+Y
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

from chan import analyze
from chan import utils
from dateutil.relativedelta import relativedelta

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
    bond = JD()
    print(bond.__module__)
  
if __name__ == "__main__":
    main()


class Computer_YTM():
    """  """

    def __init__(
        self,
        settlement_date: str = '2019/11/29',
        maturity_date: str = '2020/6/15',
        coupon: float = 0.0505,
        principal: int = 100,
        date_frequently: str = 'semi_annual',
        clean_price=50,
        YTM: float = 1.4198226
    ):
        assert date_frequently in ['annual', 'semi_annual', 'quarterly',
                                   'monthly'], "付息频率请参照['annual','quarterly','quarterly','monthly']"

        self.d_s = datetime.strptime(settlement_date, '%Y/%m/%d')
        self.d_m = datetime.strptime(maturity_date, '%Y/%m/%d')
        self.r_c = coupon
        self.pr = principal
        self.d_f = date_frequently
        self.clean_price = clean_price
        self.YTM = YTM

        self.clean_bond_price = self.pr * self.clean_price / 100
        self.dirty_bond_price:float = 0.00
        self.yield_to_maturity = 0

        self.each_interest:float = 0
        self.time_receive_interest:int = 0
        self.pay_frequency: int = 1
        self.accured_interest: float = 0
        self.interest:float=0.00

        self.cash_flow_date:list=[]
        self.previous_cash_flow_date: str = 0
        self.next_cash_flow_date: str = None

        self.days_of_next_cash_flow: int = 0
        self.days_of_maturity = (self.d_m - self.d_s)
        self.days_of_accured_interest = None
        self.years_to_maturity: float = 0.00
        
        self.TCF: float = 0
        self.DCF: float = 0      
        self.number_of_remaining_cash_flow = len(self.cash_flow_date)
        self.days_value_to_maturity = (self.d_m - self.d_s).days
        
        self._calculate_maturity()
        self._calculate_CF_date()
        self._cash_flow()
        self.show_data()

    def _calculate_maturity(self):
        """ 计算到期年限 """
        delta = self.d_m.day - self.d_s.day + \
            (self.d_m.month - self.d_s.month) * 30 + \
            (self.d_m.year - self.d_s.year) * 360
        self.years_to_maturity = delta / 360

    def _calculate_CF_date(self):
        """ 计算现金流日期 """
        start_date = self.d_s
        end_date = self.d_m
        total_year = self.years_to_maturity
        interest = []
        if self.d_f == 'annual':
            while end_date > start_date:
                insert_date = end_date.strftime("%F")
                self.cash_flow_date.insert(0, insert_date)
                end_date = self._monthdelta(end_date, -12)
                self.each_interest = self.r_c
            self.pay_frequency = 1
        elif self.d_f == 'semi_annual':
            while end_date > start_date:
                insert_date = end_date.strftime("%F")
                self.cash_flow_date.insert(0, insert_date)
                end_date = self._monthdelta(end_date, -6)
                self.each_interest = round(self.r_c / 2, 4)
            self.pay_frequency = 2
        elif self.d_f == 'quarterly':
            while end_date > start_date:
                insert_date = end_date.strftime("%F")
                self.cash_flow_date.insert(0, insert_date)
                end_date = self._monthdelta(end_date, -3)
                self.each_interest = round(self.r_c / 4, 4)
            self.pay_frequency = 4
        elif self.d_f == 'monthly':
            while end_date > start_date:
                insert_date = end_date.strftime("%F")
                self.cash_flow_date.insert(0, insert_date)
                end_date = self._monthdelta(end_date, -1)
                self.each_interest = round(self.r_c / 12, 4)
            self.pay_frequency = 12

        self.time_receive_interest = len(self.cash_flow_date)
        self.interest = [self.each_interest * 100] * self.time_receive_interest
        
        self.next_cash_flow_date = self.cash_flow_date[0]
        self.days_of_accured_interest = (self.d_s - end_date).days
        self.accured_interest = self.days_of_accured_interest / 360 * self.r_c * self.pr

        self.previous_cash_flow_date = end_date.strftime('%F')
        self.days_of_next_cash_flow = (datetime.strptime(self.cash_flow_date[0], '%Y-%m-%d') - self.d_s).days
        
        self.dirty_bond_price = self.clean_bond_price + self.accured_interest
        self.number_of_remaining_cash_flow = len(self.cash_flow_date)
        
        

    def _monthdelta(self, date, delta):
        """ 日期月份加减 """
        m, y = (date.month + delta) % 12, date.year + \
            ((date.month) + delta - 1) // 12
        if not m:
            m = 12
        d = min(
            date.day,
            [31, 29 if y % 4 == 0
             and not y % 400 == 0
             else 28, 31, 30, 31, 30, 31,
             31, 30, 31, 30, 31][m - 1])
        return date.replace(day=d, month=m, year=y)

    def _cash_flow(self):
        """ 计算每期的现流 """
        # self.TCF
        each_interest = self.interest[:]
        self.TCF = each_interest[-1] + 100
        # # self.accured_interest
        first_time_to_settlement = datetime.strptime(
            self.cash_flow_date[0], '%Y-%m-%d')
        delta = first_time_to_settlement.day - self.d_s.day + \
            (first_time_to_settlement.month - self.d_s.month) * 30
        t = delta / 360
        # self.accured_interest = delta / 360 * self.pr * self.r_c
        
        # self.DCF
        for i in range(len(self.interest)):
            self.DCF += each_interest[i] / (1 + self.YTM /
                                         self.pay_frequency)**(self.pay_frequency * t + i)

    def show_data(self):
        """ 数据展示 """
        print(f"yield to maturity：\t{self.yield_to_maturity}")
        print(f"clean bond price：\t{self.clean_bond_price}")
        print(f"accured interest：\t{self.accured_interest:,.4f}")
        print(f"dirty bond price (includes accrued)：\
                    \t{self.dirty_bond_price:,.4f}")
        print(f"duration：\t{self.yield_to_maturity}")
        print(f"modified duration：\t{self.yield_to_maturity}")
        print(f"modified convexity：\
                    \t{self.yield_to_maturity}")
        print(f"basis point value:\
                    \t{self.yield_to_maturity}")
        print(f"yield value change per 1bp increase in price：\
                    \t{self.yield_to_maturity}")
        print(f"next cash flow date：\
                    \t{self.next_cash_flow_date}")
        print(f"previous cash flow date：\
                    \t{self.previous_cash_flow_date}")
        print(f"number of days from value date to maturity：\
                    \t{self.days_value_to_maturity}")
        print(f"years to maturity:\t{self.years_to_maturity:,.4f}")
        print(f"number of days from value date to next cash flow：\
            \t{self.days_of_next_cash_flow}")
        print(f"number of days of accrued interest：\
            \t{self.days_of_accured_interest}")
        print(f"number of remaining cash flows：\
            \t{self.number_of_remaining_cash_flow}")
        

def main():
    bond = Computer_YTM(date_frequently='monthly')
  
if __name__ == "__main__":
    main()


if __name__ == '__main__':
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
        table_name = '000004'


df_all = pd.read_csv(
    r'C:\Users\Administrator\Desktop\000001.csv',
    # parse_dates=["trade_date"],
    usecols=[2, 3, 4, 5, 6, 7],
    # index_col=0
)

df_all.datetime = df_all.trade_date.apply(
    lambda x: pd.to_datetime(x))(df_all.trade_date)
print(df_all.head(2))
print(df_all.types)
columns = df_all.columns
print(columns)
json_1 = df_all.to_json(orient="index")
dict_1 = df_all.to_dict(orient="records")
print(dict_1)
print(json_1[0])
list_1 = [list(i) for i in df_all.iterlists()]

print(list_1[0:5])
df_part = df_all['trade_date']
df_part_2 = df_all[['trade_date']]
print(df_part_2.head(5))
print(type(df_part_2))
print('===============')
print(type(df_part))
print(df_part.head(5))
print('===============')
list_1 = df_part.tolist()
list_2 = df_part_2.tolist()
print(list_1[0:5])

# Update all three users with a single UPDATE query.
User.bulk_update([u1, u2, u3], fields=[User.username])
list_1 = []


database.connect()
database.create_tables([Class_4])
user = User(id=3, username='Charlie')
# print(user.save())
# print(user.id)
huey = User()
# huey.username = 'Huey'
# huey.save()
print(User.insert(username='Mickey1').execute())
# p=Class_1(id=175201, symbol='IF88',name='zhoulibing',exchange='SZSE',open_interest=0)
p = Class_4(id=175201, exchange='SZSE', symbol='IF88', datetime=datetime(1990, 12, 22), interval='1m',
            volume=490, open_interest=0, open_price=3450, high_price=3488, low_price=3450, close_price=3450)
# p_1=Class_4.insert(exchange='SZSE', symbol='IF88', datetime=datetime(1990, 12, 21), interval='1m', volume=490, open_interest=0, open_price=3450, high_price=3488, low_price=3450, close_price=3450).execute()
p.save()
Class_4.update({'symbol': "SZSE", 'interval': "d"}).execute()
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
    # 记录每个股票插入数据的截止日期
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



