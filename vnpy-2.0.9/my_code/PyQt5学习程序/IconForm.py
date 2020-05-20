import sys
from PyQt5.QtWidgets import (
    QDesktopWidget,
    QMainWindow,
    QApplication
)
from PyQt5.QtGui import QIcon
""" 
窗口的setWindowIcon方法用于设置窗口的图标，只在Windows中可用
QApplication中的setWindowIcon方法用于设置主窗口的图标和应用程序的图标，
但调用了窗口的setWindowIcon方法，QApplication中的setWindowIcon方法只能用设置应用程序的图标
"""


class IconForm(QMainWindow):
    def __init__(self):
        super(IconForm, self).__init__()
        self.initUI()

    def initUI(self):

        self.setGeometry(300, 300, 250, 250)
        # 设置主窗口标题
        self.setWindowTitle('设置窗口图标')
        # 设置窗口图标,这个程序没有成功！！！
        self.setWindowIcon(QIcon('D:\\The Road For Finacial Statics\\GitHub\\vnpy_learning\\vnpy_learning\\vnpy-2.0.9\\my_code\\PyQt5学习程序\\images\\algo.ico'))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setWindowIcon(QIcon('./images/algo.ico'))
    main = IconForm()
    main.show()
    sys.exit(app.exec_())
