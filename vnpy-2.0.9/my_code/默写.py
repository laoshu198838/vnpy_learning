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
import os 
path=Path.cwd()
print(path)
print(os.getcwd())
# print(Path.stat())
print(Path.exists("默写.py"))
# dict1 = {"AA": 1,"BB":2,"CC":3}
# print(dict1.__contains__("AA"))
# print(len(dict1))
# print(dict1.__len__())
# print(dict1.__delitem__("AA"))
# print(dict1.__getattribute__("BB"))
# # delete dict1["AA"]
# print(dict1)
# dir(dict)
# str1 = "this is string example....wow!!!"
# str2 = "Exam.txt"
# str_1 = "this is string example....wow!!!"
# print(str2.lower())
# print(str2)
# print(str_1.ljust(10, '0'))
# str3=str2.partition('.')[2]
# print(str3)

# conn = pymysql.connect(host='localhost',  # ID地址
#                        port=3306,  # 端口号
#                        user='root',  # 用户名
#                        passwd='zlb198838',  # 密码
#                        db='mytest',  # 库名
#                        charset='utf8')  # 链接字符集
# sql_query = 'select * from product;'
# # 使用pandas的read_sql_query函数执行SQL语句，并存入DataFrame
# df_read = pd.read_sql_query(sql_query, conn)
# print(df_read)
cur = conn.cursor()  # 创建游标
# df_write = pd.DataFrame({'id': [10, 27, 34, 46], 'name': ['张三', '李四', '王五', '赵六'], 'score': [80, 75, 56, 99]})
# # 将df储存为MySQL中的表，不储存index列
# df_write.to_sql('testdf',conn, index=False)
sql_insert = 'insert into 员工资料 values(6,"董事长","十一郎",123)'  # 新增SQL语句
sql_update = "update 员工资料 set 密码 = 111 WHERE ID = 6"  # 修改SQL语句
# sql_delete = "delete from 员工资料 where ID = 6"  # 删除SQL语句
try:
    cur.execute(sql_insert)  # 执行新增SQL语句
    cur.execute(sql_update)  # 执行修改SQL语句
    # cur.execute(sql_delete)  # 执行删除SQL语句
    conn.commit()  # 提交事务
except Exception as e:
    conn.rollback()  # 如果发生错误，则回滚事务
finally:
    cur.close()  # 关闭游标
    conn.close()  # 关闭数据库
