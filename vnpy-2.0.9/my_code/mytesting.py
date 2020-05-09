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

from pathlib import Path
from datetime import datetime, timedelta
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
# client = MongoClient(host='localhost', port=27017)
# path = Path(r"C:\Users\Administrator\Desktop\1")
import collections
l = ['a', 'b', 'c']
dq = collections.deque(l)

from typing import List, Tuple, Dict

from collections import namedtuple
City=namedtuple('city','name country population coordinates')
tokyo=City('Tokyo','JP','36.933',(35.689722,139.691667))
print(tokyo.name)
print(tokyo.country)
tuple_1 = ((3, 4), (2,1))
tuple_1 = [i for j in tuple_1 for i in j]
print(tuple_1)
def test(a:int, s:str, f:float, b:bool) -> Tuple[int, Tuple, Dict, bool]:
    l = a
    tup = tuple(s)
    di = {'key': f}
    bo = b
    return l, tup, di, bo
print(test(12, 'test', 1.00, 1))

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QIcon

from pymysql import connect
conn = connect(
    host='localhost',
    port=3306,
    user='root',
    password='zlb198838',
    database='stock_date_db',
    charset='utf8'
)
cs_1 = conn.cursor()


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
