# 显示控件提示信息

import sys
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QApplication,
    QPushButton,
    QWidget,
    QToolTip
)
from PyQt5.QtGui import QFont


class TooltipForm(QMainWindow):
    def __init__(self):
        super(TooltipForm, self).__init__()
        self.initUI()

    def initUI(self):
        QToolTip.setFont(QFont('SansSerif', 12))
        self.setToolTip('今天是星期五')
        self.setGeometry(600, 300, 300, 200)
        self.setWindowTitle('设置控件提示消息')

        # 添加Button
        self.button1 = QPushButton('我的按钮')
        self.button1.setToolTip('这是一个提示信息！！')
 
        # 把button1添加到水平布局里面去
        layout=QHBoxLayout()
        layout.addWidget(self.button1)

        # 把水平布局放入到QWidget窗口里面
        mainFrame = QWidget()
        mainFrame.setLayout(layout)

        self.setCentralWidget(mainFrame)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = TooltipForm()
    main.show()

    sys.exit(app.exec_())
