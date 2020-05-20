from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import sys

class QDialogDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('QDialog案例')
        self.resize(300,200)

        self.button = QPushButton(self)#这个self可以自动的把这个button绑定到QMainWindow中，
        self.button.setText('弹出对话框')
        self.button.move(50,50)
        self.button.clicked.connect(self.showDialog)

    def showDialog(self):
        dialog = QDialog()
        dialog.resize(400,300)
        button = QPushButton('确定',dialog)
        button.clicked.connect(dialog.close)
        button.move(50,50)
        dialog.setWindowTitle('对话框')
        dialog.setWindowModality(Qt.ApplicationModal)#这个表示window这个窗口的所有空间都不能用，除非关闭dialog窗口

        dialog.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = QDialogDemo()
    main.show()

    sys.exit(app.exec_())
   