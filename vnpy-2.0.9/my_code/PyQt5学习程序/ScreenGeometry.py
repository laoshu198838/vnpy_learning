import sys
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QApplication,
    QPushButton,
    QWidget
)

def onClick_Button():
    # 高度是工作区，坐标是包含标题栏的
    print(1)
    print('widget.x():%d'% widget.x())  #250
    print('widget.y():%d'% widget.y())  #200
    print('widget.width():%d'% widget.width())  #300
    print('widget.height():%d' % widget.height())   #240
    print('=========================')
    # 只是工作区的相关数据，坐标位置不包括标题栏，左边框
    print(2)
    print('widget.geometry().x():%d'% widget.geometry().x())    #251
    print('widget.geometry().y():%d'% widget.geometry().y())    #231
    print('widget.geometry().width():%d'% widget.geometry().width())    #300
    print('widget.geometry().height():%d' % widget.geometry().height()) #240
    print('=========================')
    # 高度包括标题栏，坐标不包括标题栏
    print(3)
    print('widget.frameGeometry().x():%d'% widget.frameGeometry().x())  #250
    print('widget.frameGeometry().y():%d'% widget.frameGeometry().y())  #200
    print('widget.frameGeometry().width():%d'% widget.frameGeometry().width())  #302
    print('widget.frameGeometry().height():%d' % widget.frameGeometry().height())   #272
    
app=QApplication(sys.argv)
widget = QWidget()
# 按钮添加到widget里面去
bnt=QPushButton(widget)
bnt.setText('按钮')
bnt.clicked.connect(onClick_Button)
bnt.move(24,52)
widget.resize(300,240)#设置工作区的高度，不包括标题栏的高度
widget.move(250,200)
widget.setWindowTitle('屏幕坐标系')
widget.show()
sys.exit(app.exec_())
