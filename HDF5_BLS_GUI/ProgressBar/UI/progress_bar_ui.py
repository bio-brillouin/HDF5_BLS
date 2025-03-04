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
        Form.resize(549, 183)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.l_evolution = QLabel(Form)
        self.l_evolution.setObjectName(u"l_evolution")

        self.gridLayout.addWidget(self.l_evolution, 1, 2, 1, 1)

        self.tB_Log = QTextBrowser(Form)
        self.tB_Log.setObjectName(u"tB_Log")

        self.gridLayout.addWidget(self.tB_Log, 2, 0, 1, 3)

        self.progressBar = QProgressBar(Form)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(24)

        self.gridLayout.addWidget(self.progressBar, 1, 0, 1, 2)

        self.l_curProcess = QLabel(Form)
        self.l_curProcess.setObjectName(u"l_curProcess")

        self.gridLayout.addWidget(self.l_curProcess, 0, 0, 1, 3)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Progress", None))
        self.l_evolution.setText(QCoreApplication.translate("Form", u"TextLabel", None))
        self.l_curProcess.setText(QCoreApplication.translate("Form", u"TextLabel", None))
    # retranslateUi

