# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'progress_bar.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QLabel, QProgressBar,
    QSizePolicy, QTextBrowser, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(566, 155)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.tB_Log = QTextBrowser(Form)
        self.tB_Log.setObjectName(u"tB_Log")

        self.gridLayout.addWidget(self.tB_Log, 2, 0, 1, 3)

        self.l_curProcess = QLabel(Form)
        self.l_curProcess.setObjectName(u"l_curProcess")
        font = QFont()
        font.setFamilies([u"Arial"])
        font.setPointSize(24)
        self.l_curProcess.setFont(font)

        self.gridLayout.addWidget(self.l_curProcess, 0, 0, 1, 3)

        self.progressBar = QProgressBar(Form)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setMinimumSize(QSize(250, 20))
        self.progressBar.setValue(24)
        self.progressBar.setTextVisible(True)

        self.gridLayout.addWidget(self.progressBar, 1, 0, 1, 3)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Progress", None))
        self.l_curProcess.setText(QCoreApplication.translate("Form", u"<html><head/><body><p align=\"center\"><span style=\" font-weight:700;\">Loading...</span></p></body></html>", None))
    # retranslateUi

