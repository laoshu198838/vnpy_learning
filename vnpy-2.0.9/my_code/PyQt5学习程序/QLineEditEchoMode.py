""" 
QLineEdit控件与回显模式
基本功能：输入单行的文本
EchoMode（回显模式）
1.Normal
2.NoEcho
3.Password
4.PasswordEchoOnEdit
"""

from PyQt5.QtWidgets import *
import sys

class QLineEditEchoMode(QWidget):
    def __init__(self):
        super(QLineEditEchoMode, self).__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('文本输入框回显模式')

        formLayout=QFormLayout()

        normalLineEdit=QLineEdit()
        noEchoLineEdit=QLineEdit()
        passwordLineEdit=QLineEdit()
        passwordEchoEditLineEdit=QLineEdit()

        formLayout.addRow('Normal',normalLineEdit)
        formLayout.addRow('NoEcho',noEchoLineEdit)
        formLayout.addRow('Password',passwordLineEdit)
        formLayout.addRow('PasswordEchoOnEdit',passwordEchoEditLineEdit)

        # placeholdertext
        normalLineEdit.setPlaceholderText('Normal')
        noEchoLineEdit.setPlaceholderText('NoEcho')
        passwordLineEdit.setPlaceholderText('Password')
        passwordEchoEditLineEdit.setPlaceholderText('PasswordEchoOnEdit')

        normalLineEdit.setEchoMode(QLineEdit.Normal)
        noEchoLineEdit.setEchoMode(QLineEdit.NoEcho)
        passwordLineEdit.setEchoMode(QLineEdit.Password)
        passwordEchoEditLineEdit.setEchoMode(QLineEdit.PasswordEchoOnEdit)

        self.setLayout(formLayout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = QLineEditEchoMode()
    main.show()

    sys.exit(app.exec_())