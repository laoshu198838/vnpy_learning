from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import sys


class QSlideDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('滑块控件演示')
        self.resize(300, 600)

        layout = QVBoxLayout()
        self.label = QLabel('你好 PyQt5')
        self.label.setAlignment(Qt.AlignCenter)

        self.slider = QSlider(Qt.Horizontal)
        # 设置最小值
        self.slider.setMinimum(12)
        # 设置最大值
        self.slider.setMaximum(48)
        # 设置步长
        self.slider.setSingleStep(3)
        # 设置当前值
        self.slider.setValue(18)
        # 设置刻度的位置，刻度在下方
        self.slider.setTickPosition(QSlider.TicksBelow)
        # 设置刻度的间隔
        self.slider.setTickInterval(6)
        self.slider.valueChanged.connect(self.valueChange)

        self.label1 = QLabel('你好 PyQt5')
        self.label1.setAlignment(Qt.AlignLeft)
        self.slider1 = QSlider(Qt.Vertical)
        # 设置最小值
        self.slider1.setMinimum(12)
        # 设置最大值
        self.slider1.setMaximum(48)
        # 设置步长
        self.slider1.setSingleStep(3)
        # 设置当前值
        self.slider1.setValue(18)
        # 设置刻度的位置，刻度在下方
        self.slider1.setTickPosition(QSlider.TicksBelow)
        # 设置刻度的间隔
        self.slider1.setTickInterval(6)
        self.slider1.valueChanged.connect(self.valueChange)

        layout.addWidget(self.label)
        layout.addWidget(self.label1)
        layout.addWidget(self.slider)
        layout.addWidget(self.slider1)

        self.setLayout(layout)

    def valueChange(self):
        print('当前值：%s' % self.sender().value())
        # 获取当前操作的值
        size = self.sender().value()
        self.label.setFont(QFont('Arial', size))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = QSlideDemo()
    main.show()

    sys.exit(app.exec_())

