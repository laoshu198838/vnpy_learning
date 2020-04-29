
from datetime import datetime, timedelta
import os
from pathlib import Path
import numpy as np
import pandas as pd
import time
from pymongo import MongoClient
import pymongo.errors as mongoerr


try:
    client=MongoClient(host='localhost', port=27017)
except mongoerr.ConnectionFailure as e:
    print("Could not connect: %s" % e)


def get_filename(path: str):
    """
    遍历整个文件夹，获取所有的回测文件地址和文件名称列表
    """
    stock_code_list=[]
    filename_list=[]
    for dirpath, dirnames, filenames in os.walk(str(path)):
        # os.walk() 方法用于通过在目录树中游走输出在目录中的文件名
        for filename in filenames:
            # 判断交易所
            if filename.startswith("6") or filename.startswith("8"):
                stock_code=filename[:-4] + ".SH"
                stock_code_list.append(stock_code)
            else:
                stock_code=filename[:-4] + ".SZ"
                stock_code_list.append(stock_code)
            # 判断文件后缀
            if filename.endswith(".csv"):
                filename=path + "\\" + filename
                filename_list.append(filename)

    return stock_code_list, filename_list


# 连接mongodb和相关数据库
client=MongoClient(host='localhost', port=27017)  # 连接数据库
sz_stock_db=client.SZ_STOCK_DAILY_DB              # 连接collection
sh_stock_db=client.SH_STOCK_DAILY_DB
kc_stock_db=client.KC_STOCK_DAILY_DB
# csv数据地址
path='D:\\The Road For Finacial Statics\\Python\\02.Learning Materrials\\02.Data\\02.daily_BarData'
stock_code_list, filename_list=get_filename(path)
ix=0
n=len(filename_list)

while ix < n:
    print('loading_data ', ix + 1, '/', n)
    stock_code=stock_code_list[ix][:-3]

    # 获取并处理df数据 多余的数据需要处理603893
    df_all=pd.read_csv(filename_list[ix], parse_dates=["trade_date"])
    df_all.rename(
        columns={
            "trade_date": "datetime",
            "vol": "volume", },
        inplace=True
    )
    if 'Unnamed: 0' in df_all.columns:
        df_all=df_all.drop('Unnamed: 0', axis=1)
    df_all.sort_values(['datetime'], ascending=True, inplace=True)

    # 获取db文档最后数据日期
    rows=sz_stock_db[stock_code].find().sort('datetime', -1)
    try:
        last_date=next(rows)['datetime']
    except StopIteration:
        last_date=df_all['datetime'].min() - timedelta(hours=24)

    # 在mongodb中添加新的数据
    df_part=df_all[df_all['datetime'] > last_date]
    # df转化为dict
    dict_all=df_part.to_dict(orient='records')

    # 判断存入数据是否为空
    if dict_all == []:
        print('loading_data for [' + stock_code + '] has got.')
        ix += 1
        continue

    # 把数据存入mongodb
    if stock_code.startswith("6"):
        sh_stock_db[stock_code].insert_many(dict_all)
    elif stock_code.startswith("3") or\
            stock_code_list[ix].startswith("0"):
        sz_stock_db[stock_code].insert_many(dict_all)
    else:
        kc_stock_db[stock_code].insert_many(dict_all)

    ix += 1
    print('loading_data for [' + stock_code + '] got.')
client.close()


