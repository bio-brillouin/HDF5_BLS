# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'help_function.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QLabel, QPushButton,
    QSizePolicy, QTextBrowser, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(743, 312)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.l_main = QLabel(Form)
        self.l_main.setObjectName(u"l_main")

        self.gridLayout.addWidget(self.l_main, 0, 0, 1, 1)

        self.text_docstring = QTextBrowser(Form)
        self.text_docstring.setObjectName(u"text_docstring")

        self.gridLayout.addWidget(self.text_docstring, 1, 0, 1, 1)

        self.b_close = QPushButton(Form)
        self.b_close.setObjectName(u"b_close")

        self.gridLayout.addWidget(self.b_close, 2, 0, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.l_main.setText(QCoreApplication.translate("Form", u"TextLabel", None))
        self.b_close.setText(QCoreApplication.translate("Form", u"Close", None))
    # retranslateUi

