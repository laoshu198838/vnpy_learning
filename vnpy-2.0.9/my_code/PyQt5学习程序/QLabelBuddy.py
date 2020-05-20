""" 
QLabel与伙伴关系 
mainLayout.addWidget(控件对象，rowIndex,columnIndex,row,column)
"""


import sys
from PyQt5.QtWidgets import (
    QGridLayout,
    QMainWindow,
    QApplication,
    QPushButton,
    QWidget,
    QToolTip,
    QLabel,
    QDialog,
    QLineEdit
)
from PyQt5.QtGui import QPixmap, QFont, QPalette, QIcon
from PyQt5.QtCore import Qt


class QLabelBuddy(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('QLabel与伙伴关系')
        self.setWindowIcon(QIcon(
            'D:\\The Road For Finacial Statics\\GitHub\\vnpy_learning\\vnpy_learning\\vnpy-2.0.9\\my_code\\PyQt5学习程序\\images\\algo.ico'))
        self.resize(200, 150)
        nameLabel = QLabel('&Name', self)
        nameLineEdit = QLineEdit(self)
        # 设置伙伴控件
        nameLabel.setBuddy(nameLineEdit)

        passwordLabel = QLabel('&Password', self)
        passwordLineEdit = QLineEdit(self)
        # 设置伙伴控件
        passwordLabel.setBuddy(passwordLineEdit)

        btnOK = QPushButton('&OK')
        btnCancel = QPushButton('&Cancel')

        mainLayout = QGridLayout(self)
        # 行数和列数是从0开始算，占几行是从1开始，这个地方有点特殊！！！
        mainLayout.addWidget(nameLabel, 0, 0)
        mainLayout.addWidget(nameLineEdit, 0, 1, 1, 2)

        mainLayout.addWidget(passwordLabel, 1, 0)
        mainLayout.addWidget(passwordLineEdit, 1, 1, 1, 2)

        mainLayout.addWidget(btnOK, 2, 1, )  # 默认是1
        mainLayout.addWidget(btnCancel, 2, 2, 1, 1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = QLabelBuddy()
    main.show()

    sys.exit(app.exec_())
