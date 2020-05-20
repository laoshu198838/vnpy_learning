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

import sys
from PyQt5.QtWidgets import QApplication,QWidget,QMainWindow
from Ui_first import Ui_MainWindow
import Ui_MainWinMenuToolbar
if __name__=='__main__':
    # 创建QApplication类的实例
    app = QApplication(sys.argv)
    # 生成主窗口上
    mainWindow = QMainWindow()
    # 创建类
    ui = Ui_MainWinMenuToolbar.Ui_MainWindow()
    # 主窗口添加控件
    ui.setupUi(mainWindow)
    mainWindow.show()
    sys.exit(app.exec_())
# self.pushButton.sizeHint().width()表示读取期望尺寸
# self.pushButton.sizeHint().height()表示读取期望尺寸
# self.pushButton.minimunSizeHint().width()表示读取期望尺寸
# self.pushButton.minimunSizeHint().height()表示读取期望尺寸
