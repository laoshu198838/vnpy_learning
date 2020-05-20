# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'd:\The Road For Finacial Statics\GitHub\vnpy_learning\vnpy_learning\vnpy-2.0.9\my_code\designer\MainWinAbsoluteLayout.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.webEngineView = QtWebEngineWidgets.QWebEngineView(self.centralwidget)
        self.webEngineView.setGeometry(QtCore.QRect(-140, 580, 300, 200))
        self.webEngineView.setUrl(QtCore.QUrl("about:blank"))
        self.webEngineView.setObjectName("webEngineView")
        self.webEngineView_2 = QtWebEngineWidgets.QWebEngineView(self.centralwidget)
        self.webEngineView_2.setGeometry(QtCore.QRect(50, 100, 601, 151))
        self.webEngineView_2.setUrl(QtCore.QUrl("https://www.baidu.com/"))
        self.webEngineView_2.setObjectName("webEngineView_2")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(50, 30, 71, 61))
        self.pushButton.setObjectName("pushButton")
        print(self.pushButton.sizeHint().width())
        print(self.pushButton.sizeHint().height())
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 23))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton.setText(_translate("MainWindow", "1"))
from PyQt5 import QtWebEngineWidgets
