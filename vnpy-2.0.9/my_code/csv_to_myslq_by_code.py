from datetime import datetime, timedelta
import os
import numpy as np
import pandas as pd
import time
from pymysql import connect
from collections import defaultdict


class Csv_into_mysql():

    def __init__(self):
        self.conn = connect(
            host='localhost',
            port=3306,
            user='root',
            password='zlb198838',
            database='stock_code_db',
            charset='utf8'
        )
        self.cs_1 = self.conn.cursor()

        self.stock_code_list = []
        self.filename_dir_list = []
        self.ix = 0
        self.stock = 0
        self.my_list = []
        self.error_log = {}

    def get_filename(self, path: str):
        """
        遍历整个文件夹，获取所有的回测文件地址和文件名称列表
        """
        for dirpath, dirnames, filenames in os.walk(str(path)):
            # os.walk() 方法用于通过在目录树中游走输出在目录中的文件名
            for filename in filenames:
                # 判断交易所
                if filename.startswith("6") or filename.startswith("8"):
                    self.stock_code = filename[:-4] + ".SH"
                    self.stock_code_list.append(self.stock_code)
                else:
                    self.stock_code = filename[:-4] + ".SZ"
                    self.stock_code_list.append(self.stock_code)
                # 判断文件后缀
                if filename.endswith(".csv"):
                    filename = path + "\\" + filename
                    self.filename_dir_list.append(filename)
        return self.stock_code_list, self.filename_dir_list

    def close_conn(self):
        """
        断开mysql连接
        """
        self.cs_1.close()
        self.conn.close()

    def createTable(self, stock_code:str):
        """
        创建数据库表
        sql="create table if not exists `0010`(
            id int primary key not null auto_increment,datetime date);"% self.stock_code
        sql = f"create table if not exists `{self.stock_code}`
            (id int primary key not null auto_increment,name varchar(30));"
        :return:
        """
        sql_db =f"select table_name from information_schema.tables where table_name = '{self.stock_code}';"
        if self.cs_1.execute(sql_db) == 0:
            try:
                sql = f"create table if not exists `{self.stock_code}`(\
                    id int unsigned primary key not null auto_increment,\
                    datetime date not null,\
                    open_price decimal(6, 2) not null default 0,\
                    high_price decimal(6, 2) not null default 0,\
                    low_price decimal(6, 2) not null default 0,\
                    close_price decimal(6, 2) not null default 0,\
                    volume decimal(30, 10) default 0,\
                    amount decimal(30, 10) default 0,\
                    index(datetime)\
                );"
                self.cs_1.execute(sql)
                self.conn.commit()
                print('create table ok!')
            except Exception as e:
                # 未完成！！
                list = []
                list.append(e)
                e = self.error_log(self.stock_code)
                print(e)
                print(self.error_log)
                print(list)
        else:
            return
    
    def myList(self, filename_dir: list):
        """
        import csv:
        open	high	low	    close	vol	        amount
        12.82	12.89	12.55	12.61	825348.14	1047282.4
        12.75	12.97	12.66	12.97	518365.04	663197.628

        return: new_list，
        [
        (1991-04-04  48.76  48.76  48.76  48.76  3.0  15.0),
        (1991-04-05  48.52  48.52  48.52  48.52  2.0  10.0),
        (1991-04-08  48.04  48.04  48.04  48.04  2.0  10.0),
        ...]
        """
        columns=['trade_date','open','high','low','close','vol','amount']
        self.stock_code = self.stock_code_list[self.ix][:-3]
        # [2, 3, 4, 5, 6, 10, 11]
        # 获取并处理df数据
        try:
            df_all = pd.read_csv(
                self.filename_dir_list[self.ix],
                usecols=columns,
                sep=','
            )
        except Exception as e:
            print(e)
            return

        df_all.set_index('trade_date', inplace=True, drop=False)
        df_all.rename(
            columns={
                "trade_date": "datetime",
                "vol": "volume",
            },
            inplace=True
        )
       
        # 把数字日期格式转化为指定日期格式
        df_all.datetime = pd.to_datetime(df_all.datetime, format='%Y%m%d')
        df_all.sort_values(by=['datetime'], ascending=True, inplace=True)

        # 获取mysql中已有数据的截止日期
        self.cs_1.execute(f"select max(datetime) from `{self.stock_code}`;")
        rows = self.cs_1.fetchone()[0]
        try:
            last_date = pd.Timestamp(rows + timedelta(hours=24))
        except:
            last_date = df_all['datetime'].min() - timedelta(hours=24)

        # 筛选出需要保存的最新数据，并删除多余的列datetime
        df_part = df_all[df_all['datetime'] > last_date]
        df_part = df_part.drop('datetime', axis=1)
        # 处理其中的NaN值
        if df_part.isnull().values.any() == True:
            df_part.fillna(0,inplace=True)
        
        # 判断存入数据是否为空
        if len(df_part) == 0:
            print(self.stock_code + ' has no new data to insert!.')
            return

        # df转化为[(),()]
        self.my_list = [tuple(i) for i in df_part.itertuples()]
        print(self.my_list[0])
        return self.my_list

    def myInsert(self, newList: list):
        '''
        数据库插入
        :param newList: 传入的列表数据
        批量添加数据，！！！！！数据格式必须list[tuple(),tuple(),tuple()]
        :return:
        '''

        try:
            # 要插入的数据
            sql = f"insert into `{self.stock_code}`\
                (datetime,open_price,high_price,low_price,close_price,volume,amount)\
                    values(%s,%s,%s,%s,%s,%s,%s)"
            self.cs_1.executemany(sql, newList)  # 执行插入数据
            self.conn.commit()

        except Exception as e:
            print(e)

    def print_info(self, info:str):
        """ 打印过程信息 """
        n = len(self.filename_dir_list)
        print(str(self.ix + 1), '/', str(n) + ':(' +
              self.stock_code + ') ' + info)

    def Insert_all_file(self, path: str):
        """
        插入文件夹中所有的csv文件
        """
        self.stock_code_list, self.filename_dir_list = self.get_filename(path)
        n = len(self.filename_dir_list)
        
        while self.ix < n:
            # 循环插入csv文件
            self.stock_code = self.stock_code_list[self.ix][:-3]
            self.createTable(self.stock_code)
            self.print_info('starting insert')
            self.myList(self.filename_dir_list)
            self.myInsert(self.my_list)
            self.print_info('insert ok.\n')
            self.ix += 1


def main():
    # 创建数据表
    csv_to_sql = Csv_into_mysql()
    # 选择要插入的数据的文件夹地址
    path = 'D:\\The Road For Finacial Statics\\Python\\02.Learning Materrials\\02.Data\\02.daily_BarData'
    csv_to_sql.Insert_all_file(path)
    csv_to_sql.close_conn()


if __name__ == '__main__':
    main()
