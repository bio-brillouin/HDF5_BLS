# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'algorithmCreator.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QGridLayout, QLabel, QLineEdit, QListView,
    QPushButton, QSizePolicy, QTabWidget, QTextEdit,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(600, 500)
        self.gridLayout = QGridLayout(Dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.tabWidget = QTabWidget(Dialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.gridLayout_2 = QGridLayout(self.tab)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.l_NameAlgorithm = QLabel(self.tab)
        self.l_NameAlgorithm.setObjectName(u"l_NameAlgorithm")

        self.gridLayout_2.addWidget(self.l_NameAlgorithm, 0, 0, 1, 3)

        self.le_Author = QLineEdit(self.tab)
        self.le_Author.setObjectName(u"le_Author")

        self.gridLayout_2.addWidget(self.le_Author, 3, 0, 1, 3)

        self.le_NameAlgorithm = QLineEdit(self.tab)
        self.le_NameAlgorithm.setObjectName(u"le_NameAlgorithm")

        self.gridLayout_2.addWidget(self.le_NameAlgorithm, 1, 0, 1, 3)

        self.te_Description = QTextEdit(self.tab)
        self.te_Description.setObjectName(u"te_Description")

        self.gridLayout_2.addWidget(self.te_Description, 5, 0, 1, 3)

        self.l_Description = QLabel(self.tab)
        self.l_Description.setObjectName(u"l_Description")

        self.gridLayout_2.addWidget(self.l_Description, 4, 0, 1, 3)

        self.l_Author = QLabel(self.tab)
        self.l_Author.setObjectName(u"l_Author")

        self.gridLayout_2.addWidget(self.l_Author, 2, 0, 1, 3)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.gridLayout_3 = QGridLayout(self.tab_2)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.lst_Algorithm = QListView(self.tab_2)
        self.lst_Algorithm.setObjectName(u"lst_Algorithm")

        self.gridLayout_3.addWidget(self.lst_Algorithm, 0, 0, 1, 2)

        self.lst_Functions = QListView(self.tab_2)
        self.lst_Functions.setObjectName(u"lst_Functions")

        self.gridLayout_3.addWidget(self.lst_Functions, 0, 2, 1, 2)

        self.pushButton = QPushButton(self.tab_2)
        self.pushButton.setObjectName(u"pushButton")

        self.gridLayout_3.addWidget(self.pushButton, 1, 0, 2, 2)

        self.b_MoveUp = QPushButton(self.tab_2)
        self.b_MoveUp.setObjectName(u"b_MoveUp")

        self.gridLayout_3.addWidget(self.b_MoveUp, 3, 0, 1, 1)

        self.b_MoveDown = QPushButton(self.tab_2)
        self.b_MoveDown.setObjectName(u"b_MoveDown")

        self.gridLayout_3.addWidget(self.b_MoveDown, 3, 1, 1, 1)

        self.b_AddBefore = QPushButton(self.tab_2)
        self.b_AddBefore.setObjectName(u"b_AddBefore")

        self.gridLayout_3.addWidget(self.b_AddBefore, 1, 2, 3, 1)

        self.b_AddAfter = QPushButton(self.tab_2)
        self.b_AddAfter.setObjectName(u"b_AddAfter")

        self.gridLayout_3.addWidget(self.b_AddAfter, 1, 3, 3, 1)

        self.tabWidget.addTab(self.tab_2, "")

        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.l_NameAlgorithm.setText(QCoreApplication.translate("Dialog", u"Name of the algorithm", None))
        self.l_Description.setText(QCoreApplication.translate("Dialog", u"Description of the algorithm", None))
        self.l_Author.setText(QCoreApplication.translate("Dialog", u"Author of the algorithm", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("Dialog", u"Tab 1", None))
        self.pushButton.setText(QCoreApplication.translate("Dialog", u"Delete step", None))
        self.b_MoveUp.setText(QCoreApplication.translate("Dialog", u"Move Up", None))
        self.b_MoveDown.setText(QCoreApplication.translate("Dialog", u"Move Down", None))
        self.b_AddBefore.setText(QCoreApplication.translate("Dialog", u"Add Step Before", None))
        self.b_AddAfter.setText(QCoreApplication.translate("Dialog", u"Add Step After", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("Dialog", u"Tab 2", None))
    # retranslateUi

