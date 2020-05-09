from datetime import datetime, timedelta
import os
import numpy as np
import pandas as pd
import time
from pymysql import connect
from collections import defaultdict


class Mysql_load_data():

    def __init__(self):
        pass

    def conn_db(self, db: str):
        self.conn = connect(
            host='localhost',
            port=3306,
            user='root',
            password='zlb198838',
            database=db,
            charset='utf8'
        )
        self.cs = self.conn.cursor()

    def load_stock_data(
        self,
        stock_code: str,
        start_date: str,
        end_date: str
    ):
        """ 
        return
        id    datetime  ...             volume             amount
        0  2126  2000-01-04  ...   82161.0000000000  147325.3568000000
        1  2127  2000-01-05  ...   93993.0000000000  173475.1588000000
        """

        self.conn_db('stock_code_db')
        sql = f"select * from `{stock_code}` where datetime between {start_date} and {end_date};"
        self.cs.execute(sql)
        stock_data = self.cs.fetchall()
        column = ['id', 'datetime', 'open_price', 'high_price',
                  'low_price', 'close_price', 'volume', 'amount']
        # tuple转DataFrame
        stock_df = pd.DataFrame(list(stock_data), columns=column)
        stock_df.drop(['id'], axis=1, inplace=True)

        return stock_df

    def load_date_data(self, date: str):
        """ 
        return
        stock_code open_price  ...            volume            amount
        000002      18.50      ...  10940.0000000000  20340.0000000000
        000004      18.00      ...   6427.0000000000  11494.0000000000
        """
        self.conn_db('stock_date_db')
        sql = f"select * from `{date}`;"
        self.cs.execute(sql)
        stock_date_data = self.cs.fetchall()
        column = ['id', 'stock_code', 'open_price', 'high_price',
                  'low_price', 'close_price', 'volume', 'amount']
        # tuple转DataFrame
        stock_df = pd.DataFrame(list(stock_date_data), columns=column)
        stock_df.drop(['id'], axis=1, inplace=True)
        print(stock_df.head(5))
        return stock_df


def main():
    loading_data = Mysql_load_data()
    loading_data.load_stock_data("000001", "20000101", "20000131")
    loading_data.load_date_data('19930526')


if __name__ == "__main__":
    main()
