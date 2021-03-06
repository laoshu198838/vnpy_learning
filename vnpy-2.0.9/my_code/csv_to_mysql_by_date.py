from datetime import datetime, timedelta
import os
import numpy as np
import pandas as pd
import time
from pymysql import connect
from collections import defaultdict
# from typing import list, tuple, str


class Csv_into_mysql():
    def __init__(self):
        self.conn = connect(
            host='localhost',
            port=3306,
            user='root',
            password='zlb198838',
            database='stock_date_db',
            charset='utf8'
        )
        self.cs = self.conn.cursor()

        self.stock_code_list = []
        self.filename_dir_list = []
        self.ix = 0
        self.stock = 0
        self.my_dict = []
        self.error_log = {}
        self.date_table = []

        self.sql_tuple = []
        self.row = 0
        self.insert_date = None
        self.update_date = None

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
        self.cs.close()
        self.conn.close()

    def createTable(self, date: str):
        """
        创建数据库表
        sql="create table if not exists `0010`(
            id int primary key not null auto_increment,datetime date);"% self.stock_code
        sql = f"create table if not exists `{self.stock_code}`
            (id int primary key not null auto_increment,name varchar(30));"
        :return:
        """
        sql_db = f"select table_name from info_1rmation_schema.tables where table_name = '{date}';"
        if self.cs.execute(sql_db) == 0:
            try:
                sql = f"create table if not exists `{date}`(\
                    id int unsigned primary key not null auto_increment,\
                    stock_code varchar(8) not null,\
                    open_price decimal(6, 2) not null default 0,\
                    high_price decimal(6, 2) not null default 0,\
                    low_price decimal(6, 2) not null default 0,\
                    close_price decimal(6, 2) not null default 0,\
                    volume decimal(30, 10) default 0,\
                    amount decimal(30, 10) default 0,\
                    index(stock_code)\
                );"

                self.cs.execute(sql)
                print('create table ok!')
            except Exception as e:
                print(e)

        else:
            return

    def myList(self, filename_dir: list):
        """
        import csv:
        ts_code     trade_date open	    high	low	    close	vol	        amount
        000001.SZ   20200403   12.82	12.89	12.55	12.61	825348.14	1047282.40
        000001.SZ   20200402   12.75	12.97	12.66	12.97	518365.04	663197.628

        return: self.data_table = [19910404,19910405,19910408,...]
        return: self.sql_tuple，
        [
        (0  000001 48.76  48.76  48.76  48.76  3.0  15.0),
        (0  000001 48.52  48.52  48.52  48.52  2.0  10.0),
        (0  000001 48.04  48.04  48.04  48.04  2.0  10.0),
        ...]
        """
        columns = [
            'ts_code', 'trade_date',
            'open', 'high',
            'low', 'close',
            'vol',
            'amount'
        ]

        # 获取并处理df数据
        try:
            df_all = pd.read_csv(
                self.filename_dir_list[self.ix],
                usecols=columns,
            )
        except Exception as e:
            print(e)
            return
        # 处理其中的NaN值
        if df_all.isnull().values.any() == True:
            df_all.fillna(0, inplace=True)
        # 改变列名
        df_all.rename(columns={
            "trade_date": "datetime",
            "vol": "volume",
        },
            inplace=True)
        
        df_all['ts_code'] = df_all['ts_code'].map(lambda x: x.split('.')[0])
        df_all['datetime_Temp'] = pd.to_datetime(
            df_all.datetime, format='%Y%m%d')
        
        # 筛选出需要插入的数据
        # print(df_all.head(-5))
        df_all = df_all[df_all['datetime_Temp'] >= self.insert_date]
        df_all.drop(['datetime_Temp'], axis=1, inplace=True)
        # print(df_all.head(5))
        # 判断存入数据是否为空，跳出本次循环。
        if len(df_all) == 0:
            print(self.stock_code + ' has no new data to insert!.')
            return

        # 利用datetime得到股票每个交易日的日期，用于生成日期表名
        df_all.sort_values(by=['datetime'], ascending=True, inplace=True)
        # print(df_all)
        self.date_table = df_all['datetime'].values.tolist()
        df_all = df_all.drop('datetime', axis=1)

        # mysql中的id可以全部用0作为使用默认值的替代品
        df_all['id'] = 0
        df_all.set_index('id', inplace=True)

        # df转化为[(),()]
        self.sql_tuple = [tuple(i) for i in df_all.itertuples()]
        # print(self.date_table[0:5])
        # print(self.sql_tuple[0:5])
        return self.date_table, self.sql_tuple

    def record_insert_date(self, stock: str, date: str):
        """ 
        记录每个股票插入数据的截止日期
        """
        try:
            sql_1 = f"select count(*) from stock_insert_date_record where stock_code={stock};"
            self.cs.execute(sql_1)
            count = self.cs.fetchone()[0]
            if count == 0:
                sql_tuple = (stock, date)
                sql_2 = f"insert into stock_insert_date_record (stock_code,expiration_date) values (%s,%s);"
                self.cs.execute(sql_2, sql_tuple)
            else:
                sql_3 = f"update stock_insert_date_record set expiration_date={date} where stock_code={stock};"
                self.cs.execute(sql_3)
            self.conn.commit()
        except Exception as e:
            print(e)

    def find_insert_date(self, stock: str):
        """ 
        查找股票插入的起始日期
        """
        sql_1 = f"select expiration_date from stock_insert_date_record where stock_code={stock};"
        if self.cs.execute(sql_1) == 0:
            self.insert_date = datetime(1990, 1, 1)
        else:
            self.insert_date = self.cs.fetchone()[0] + timedelta(days=1)
        self.insert_date = pd.Timestamp(self.insert_date)
        
        return self.insert_date

    def myInsert(self, date: list, sql_tuple: list):
        '''
        数据库插入
        :param newList: 传入的列表数据
        批量添加数据，！！！！！数据格式必须list[tuple(),tuple(),tuple()]
        :return:            
        '''
        try:
            # 单个股票对日期进行存储
            while self.row < len(date):
                n = self.row + 1
                print(str(n) + '/' + str(len(date)))
                self.createTable(date[self.row])
                sql = f"insert into `{date[self.row]}`\
                    (id,stock_code,open_price,high_price,low_price,close_price,volume,amount)\
                    values(%s,%s,%s,%s,%s,%s,%s,%s);"
                # 执行插入数据
                self.cs.execute(sql, sql_tuple[self.row])
                self.conn.commit()
                self.row += 1
            self.update_date = date[-1]
            self.record_insert_date(self.stock, self.update_date)
            self.row = 0
            self.conn.commit()
            self.record_insert_date(self.stock_code, date[-1])

        except Exception as e:
            print(e)

    def print_info_1(self, info_1: str):
        """ 打印过程信息 """
        n = len(self.filename_dir_list)
        print(str(self.ix + 1), '/',
              str(n) + ':(' + self.stock_code + ') ' + info_1)

    def Insert_all_file(self, path: str):
        """
        插入文件夹中所有的csv文件
        """
        self.stock_code_list, self.filename_dir_list = self.get_filename(path)
        n = len(self.stock_code_list)

        while self.ix < n:
            # 循环插入csv文件
            
            self.stock_code = self.stock_code_list[self.ix][:-3]
            self.print_info_1('starting insert')
            self.find_insert_date(self.stock_code)
            self.myList(self.filename_dir_list)
            self.myInsert(self.date_table, self.sql_tuple)
            self.print_info_1('insert ok.\n')
            self.ix += 1

    def delete_repeat_data(self):
        """ 
        删除表中的重复数据
        table_name=(('19910101',),('19910102',)...)
        stock_id=((1,),(2,)...)
        """
        # (1) 选出所有的表名
        sql_1 = "show tables;"
        self.cs.execute(sql_1)
        table_name = self.cs.fetchall()
        for i in range(len(table_name)):
            # (2) 查看每个表中是否有重复数据
            info_1=(str(i),'.检查表',table_name[i][0],'是否存在重复数据')
            print(''.join(info_1))
            
            sql_2=f"select min(id),stock_code as id from `{table_name[i][0]}` group by stock_code having count(stock_code) > 1;"         
            self.cs.execute(sql_2)
            stock_id = self.cs.fetchall()
            
            # (3) 删除重复数据
            if len(stock_id) != 0:
                info_2=(table_name[i][0],'存在重复数据',str(len(stock_id)),'处')
                print(''.join(info_2))
                
                for j in range(len(stock_id)):
                    info_3=('删除第', str(j + 1),'处')
                    print(''.join(info_3))
                    sql_3 = f"delete from `{table_name[i][0]}` where id not in ({stock_id[j][0]}) and stock_code={stock_id[j][1]};"
                    self.cs.execute(sql_3)
                self.conn.commit()



def main():
    # 创建数据表
    csv_to_sql = Csv_into_mysql()
    # 选择要插入的数据的文件夹地址
    path = 'D:\\The Road For Finacial Statics\\Python\\02.Learning Materrials\\02.Data\\02.daily_BarData'
    csv_to_sql.Insert_all_file(path)
    
    csv_to_sql.delete_repeat_data()
    csv_to_sql.close_conn()

if __name__ == '__main__':
    main()
    