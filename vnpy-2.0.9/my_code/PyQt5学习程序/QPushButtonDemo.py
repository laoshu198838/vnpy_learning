from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import sys


class QPushButtonDemo(QDialog):
    def __init__(self):
        super(QPushButtonDemo, self).__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('QPushButton Demo')
        self.resize(300, 200)
        self.setWindowIcon(QIcon(
            'D:\\The Road For Finacial Statics\\GitHub\\vnpy_learning\\vnpy_learning\\vnpy-2.0.9\\my_code\\PyQt5学习程序\\images\\algo.ico'))
        layout = QVBoxLayout()

        self.button1 = QPushButton('第1个按钮')
        self.button1.setText('First Button1')#改变了第一个按钮这个名称
        self.button1.setCheckable(True)  # 可被选中
        self.button1.toggle()  # 开关按钮，类似那种有凹凸效果的按钮
        self.button1.clicked.connect(
            lambda: self.onClickedButton(self.button1)
        )  # 利用lambda把传参的权限收回到我们自己手中，如果不收回来，这个方法只需要传函数的名车就行了，利用lambda可以自己把参数传入进去
        self.button1.clicked.connect(self.buttonState)
        layout.addWidget(self.button1)

        self.button2 = QPushButton('图像按钮')
        self.button2.setIcon(QIcon(QPixmap('D:\\The Road For Finacial Statics\\GitHub\\vnpy_learning\\vnpy_learning\\vnpy-2.0.9\\my_code\\PyQt5学习程序\\images\\11.jpg')))  # 相对地址不可用
        # 这个QPixmap估计是可以把其他格式的图片转化为QIcon要求的格式
        self.button2.clicked.connect(
            lambda: self.onClickedButton(self.button2))
        layout.addWidget(self.button2)

        self.button3=QPushButton('不可用的按钮')
        self.button3.setEnabled(False)#设置成灰色不可用
        layout.addWidget(self.button3)

        self.button4=QPushButton('&MyButton')
        self.button4.setDefault(True)
        self.button4.clicked.connect(lambda : self.onClickedButton(self.button4))
        layout.addWidget(self.button4)

        self.setLayout(layout)

    def onClickedButton(self, bnt):
        print('被按下的按钮是<' + bnt.text() + '>')

    def buttonState(self):
        if self.button1.isChecked():
            print('按钮1已经被选中')
        else:
            print('按钮1未被选中')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = QPushButtonDemo()
    main.show()

    sys.exit(app.exec_())
