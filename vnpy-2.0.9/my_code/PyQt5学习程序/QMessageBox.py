""" 
消息对话框：QMessageBox
1.关于对话框
2.错误对话框
3.警告对话框
4.提问对话框
5.消息对话框

2点差异
1.显示的对话框图标可能不同
2.显示的按钮是不一样的

"""
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import sys


class QMessageBoxDemo(QWidget):
    def __init__(self):
        super(QMessageBoxDemo, self).__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('消息对话框')
        self.resize(300, 400)

        layout = QVBoxLayout()
        # self.button1 = QPushButton(self)这个self可以把这个button绑定到QMainWindow中，如果再用self.setLayout(layout)就会出现
        # QWidget::setLayout: Attempting to set QLayout "" on QMessageBoxDemo "", which already has a layout
        self.button1 = QPushButton(self)
        self.button1.setText('显示关于对话框')
        self.button1.clicked.connect(self.showDialog)

        self.button2 = QPushButton(self)
        self.button2.setText('显示消息对话框')
        self.button2.clicked.connect(self.showDialog)

        self.button3 = QPushButton(self)
        self.button3.setText('显示警告对话框')
        self.button3.clicked.connect(self.showDialog)

        self.button4 = QPushButton(self)
        self.button4.setText('显示错误对话框')
        self.button4.clicked.connect(self.showDialog)

        self.button5 = QPushButton(self)
        self.button5.setText('显示提问对话框')
        self.button5.clicked.connect(self.showDialog)

        layout.addWidget(self.button1)
        layout.addWidget(self.button2)
        layout.addWidget(self.button3)
        layout.addWidget(self.button4)
        layout.addWidget(self.button5)
        self.setLayout(layout)

    def showDialog(self):
        text = self.sender().text()
        print(self.sender())
        if text == '显示关于对话框':
            QMessageBox.about(self, '关于', '这是一个关于对话框')
        elif text == '显示消息对话框':
            reply = QMessageBox.information(self, '消息', '这是一个消息对话框', QMessageBox.Yes | QMessageBox.No,)
            print(reply)
        elif text == '显示警告对话框':
            reply = QMessageBox.warning(self, '警告', '这是一个警告对话框', QMessageBox.Yes | QMessageBox.No,)
            print(reply)
        elif text == '显示错误对话框':
            reply = QMessageBox.critical(self, '错误', '这是一个警告错误', QMessageBox.Yes | QMessageBox.No,)
            print(reply)
        elif text == '显示提问对话框':
            reply = QMessageBox.question(self, '提问', '这是一个提问对话框', QMessageBox.Yes | QMessageBox.No,)
            print(reply)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = QMessageBoxDemo()
    main.show()

    sys.exit(app.exec_())
