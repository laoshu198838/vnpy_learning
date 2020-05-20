"""
QLabel控件：
setAlignment(): 设置文本对齐方式
setIndent():设置文本缩进
text():获取文本内容
setBuddy():设置伙伴关系
setText():设置文本内容
selectedText():返回所选择的内容
setWordWrap():设置是否允许换行
"""
import sys
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QMainWindow,
    QApplication,
    QPushButton,
    QWidget,
    QToolTip,
    QLabel
)
from PyQt5.QtGui import QPixmap, QFont, QPalette
from PyQt5.QtCore import Qt
# 有些常量是在Qt里面如Qt.blue
# QPixmap表示显示图片


class QLabelDemo(QWidget):
    def __init__(self):
        super(QLabelDemo, self).__init__()
        self.initUI()

    def initUI(self):
        label_1 = QLabel()
        label_2 = QLabel()
        label_3 = QLabel()
        label_4 = QLabel()

        label_1.setText("<font color=yellow>这是一个文本标签.</font>")  # 设置字体大小和颜色
        label_1.setAutoFillBackground(True)  # 自动填充背景
        palette = QPalette()  # 创建调色板
        palette.setColor(QPalette.Window, Qt.blue)  # 设置背景色
        label_1.setPalette(palette)  # 对标签使用调色板
        label_1.setAlignment(Qt.AlignCenter)  # 对文本使用居中对齐

        label_2.setText("<a href='#'>欢迎使用Python GUI程序</a>")  # 这个为什么这么写呢！！！！

        label_3.setAlignment(Qt.AlignCenter)  # 居中对齐

        label_3.setToolTip('这是一个图片')
        label_3.setPixmap(QPixmap(
            'D:\\The Road For Finacial Statics\\GitHub\\vnpy_learning\\vnpy_learning\\vnpy-2.0.9\\my_code\\PyQt5学习程序\\images\\11.jpg'))  # 不知道为什么用相对地址不行

        # 如果设置为True，用浏览器打开网页，如果设为false，调用槽函数
        label_4.setOpenExternalLinks(True)
        label_4.setText(
            "<a href='http://item.jd.com/12417265.html'>感谢关注《python从菜鸟到高手》</a>")
        # 向右对齐
        label_4.setAlignment(Qt.AlignRight)
        # 提示文字
        label_4.setToolTip('这是一个超链接')

        # 垂直对齐布局
        vbox = QVBoxLayout()
        vbox.addWidget(label_1)  # 添加标签
        vbox.addWidget(label_2)
        vbox.addWidget(label_3)
        vbox.addWidget(label_4)
        # 标签绑定信号槽
        label_2.linkHovered.connect(self.linkHovered)
        label_4.linkActivated.connect(self.linkclicked)
        
        # 把vbox的布局放到self实例里面去
        self.setLayout(vbox)
        self.setWindowTitle("QLabel控件演示")

    def linkHovered(self):
        print("当鼠标滑过label_2标签时，触发事件")

    def linkclicked(self):
        print("当鼠标单击label_4标签时，触发事件")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = QLabelDemo()
    main.show()

    sys.exit(app.exec_())
