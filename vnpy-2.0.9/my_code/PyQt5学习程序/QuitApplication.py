import sys
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QApplication,
    QPushButton,
    QWidget
)

class QuitApplication(QMainWindow):
    def __init__(self):
        super(QuitApplication, self).__init__()
        self.resize(400,300)
        self.setWindowTitle('退出应用程序')

        # 添加Button
        self.button1 = QPushButton('退出应用程序')
        # 将信号槽关联
        self.button1.clicked.connect(self.onClick_Button)

        # 把button1添加到水平布局里面去
        layout=QHBoxLayout()
        layout.addWidget(self.button1)
        
        # 把水平布局放入到QWidget窗口里面
        mainFrame = QWidget()
        mainFrame.setLayout(layout)

        self.setCentralWidget(mainFrame)


    # 按钮单击事件的方法（自定义)
    def onClick_Button(self):
        # 程序发送消息
        sender = self.sender()
        # text是输出button的文本，
        print(sender.text() + '按钮被按下')
        # 应用程序的实例
        app=QApplication.instance()
        
        app.quit()

if __name__=='__main__':
    # 创建QApplication类的实例
    app = QApplication(sys.argv)
    # 创建类
    main = QuitApplication()
    main.show()
    sys.exit(app.exec_())