from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import sys


class QFileDialogDemo(QWidget):
    def __init__(self):
        super(QFileDialogDemo, self).__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('QFileDialog例子')
        self.resize(300, 400)
        layout = QVBoxLayout()
        self.button = QPushButton('加载图片')
        self.button.clicked.connect(self.loadImage)
        layout.addWidget(self.button)

        self.imageLabel = QLabel()
        layout.addWidget(self.imageLabel)

        self.button2 = QPushButton('加载文本文件')
        self.button2.clicked.connect(self.loadText)
        layout.addWidget(self.button2)

        self.contents = QTextEdit()
        layout.addWidget(self.contents)

        self.setLayout(layout)

    def loadImage(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, '打开文件', '.', '图像文件(*.jpg *.png)')
        self.imageLabel.setPixmap(QPixmap(fname))

    def loadText(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setFilter(QDir.Files)
        print(1)
        if dialog.exec():
            filenames = dialog.selectedFiles()
            # print(filenames)文件地址列表
            f = open(filenames[0], 'r', encoding='UTF-8')
            # 要加encoding='UTF-8'要不然会报错：'gbk' codec can't decode byte 0xbc in position 15: illegal multibyte sequence
            with f:
                data = f.read()
                self.contents.setText(data)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = QFileDialogDemo()
    main.show()

    sys.exit(app.exec_())
