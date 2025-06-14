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
    QGridLayout, QHeaderView, QLabel, QLineEdit,
    QListView, QPushButton, QSizePolicy, QTabWidget,
    QTextEdit, QTreeView, QWidget)
import Icons_rc

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(700, 500)
        self.gridLayout = QGridLayout(Dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.tabWidget = QTabWidget(Dialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab_Properties = QWidget()
        self.tab_Properties.setObjectName(u"tab_Properties")
        self.gridLayout_2 = QGridLayout(self.tab_Properties)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.l_NameAlgorithm = QLabel(self.tab_Properties)
        self.l_NameAlgorithm.setObjectName(u"l_NameAlgorithm")

        self.gridLayout_2.addWidget(self.l_NameAlgorithm, 0, 0, 1, 2)

        self.le_NameAlgorithm = QLineEdit(self.tab_Properties)
        self.le_NameAlgorithm.setObjectName(u"le_NameAlgorithm")

        self.gridLayout_2.addWidget(self.le_NameAlgorithm, 1, 0, 1, 1)

        self.le_Version = QLineEdit(self.tab_Properties)
        self.le_Version.setObjectName(u"le_Version")
        self.le_Version.setMinimumSize(QSize(0, 0))
        self.le_Version.setMaximumSize(QSize(100, 16777215))

        self.gridLayout_2.addWidget(self.le_Version, 1, 2, 1, 1)

        self.te_Description = QTextEdit(self.tab_Properties)
        self.te_Description.setObjectName(u"te_Description")

        self.gridLayout_2.addWidget(self.te_Description, 7, 0, 1, 3)

        self.l_Version = QLabel(self.tab_Properties)
        self.l_Version.setObjectName(u"l_Version")

        self.gridLayout_2.addWidget(self.l_Version, 0, 2, 1, 1)

        self.l_Description = QLabel(self.tab_Properties)
        self.l_Description.setObjectName(u"l_Description")

        self.gridLayout_2.addWidget(self.l_Description, 6, 0, 1, 3)

        self.l_Author = QLabel(self.tab_Properties)
        self.l_Author.setObjectName(u"l_Author")

        self.gridLayout_2.addWidget(self.l_Author, 2, 0, 1, 1)

        self.le_Author = QLineEdit(self.tab_Properties)
        self.le_Author.setObjectName(u"le_Author")

        self.gridLayout_2.addWidget(self.le_Author, 3, 0, 1, 3)

        self.tabWidget.addTab(self.tab_Properties, "")
        self.tab_Algorithm = QWidget()
        self.tab_Algorithm.setObjectName(u"tab_Algorithm")
        self.gridLayout_3 = QGridLayout(self.tab_Algorithm)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.b_AddBefore = QPushButton(self.tab_Algorithm)
        self.b_AddBefore.setObjectName(u"b_AddBefore")
        icon = QIcon()
        icon.addFile(u":/Buttons/icon/add_above.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.b_AddBefore.setIcon(icon)
        self.b_AddBefore.setIconSize(QSize(25, 25))

        self.gridLayout_3.addWidget(self.b_AddBefore, 3, 4, 1, 1)

        self.lst_Functions = QListView(self.tab_Algorithm)
        self.lst_Functions.setObjectName(u"lst_Functions")

        self.gridLayout_3.addWidget(self.lst_Functions, 0, 4, 1, 3)

        self.b_MoveDown = QPushButton(self.tab_Algorithm)
        self.b_MoveDown.setObjectName(u"b_MoveDown")
        icon1 = QIcon()
        icon1.addFile(u":/Buttons/icon/move_down.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.b_MoveDown.setIcon(icon1)
        self.b_MoveDown.setIconSize(QSize(25, 25))

        self.gridLayout_3.addWidget(self.b_MoveDown, 3, 2, 1, 1)

        self.b_Delete = QPushButton(self.tab_Algorithm)
        self.b_Delete.setObjectName(u"b_Delete")
        icon2 = QIcon()
        icon2.addFile(u":/Buttons/icon/bin.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.b_Delete.setIcon(icon2)
        self.b_Delete.setIconSize(QSize(25, 25))

        self.gridLayout_3.addWidget(self.b_Delete, 3, 1, 1, 1)

        self.b_MoveUp = QPushButton(self.tab_Algorithm)
        self.b_MoveUp.setObjectName(u"b_MoveUp")
        icon3 = QIcon()
        icon3.addFile(u":/Buttons/icon/move_up.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.b_MoveUp.setIcon(icon3)
        self.b_MoveUp.setIconSize(QSize(25, 25))

        self.gridLayout_3.addWidget(self.b_MoveUp, 3, 0, 1, 1)

        self.b_AddAfter = QPushButton(self.tab_Algorithm)
        self.b_AddAfter.setObjectName(u"b_AddAfter")
        icon4 = QIcon()
        icon4.addFile(u":/Buttons/icon/add_below.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.b_AddAfter.setIcon(icon4)
        self.b_AddAfter.setIconSize(QSize(25, 25))

        self.gridLayout_3.addWidget(self.b_AddAfter, 3, 6, 1, 1)

        self.b_Help = QPushButton(self.tab_Algorithm)
        self.b_Help.setObjectName(u"b_Help")
        icon5 = QIcon()
        icon5.addFile(u":/Buttons/icon/help.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.b_Help.setIcon(icon5)
        self.b_Help.setIconSize(QSize(25, 25))

        self.gridLayout_3.addWidget(self.b_Help, 3, 5, 1, 1)

        self.tv_algorithm = QTreeView(self.tab_Algorithm)
        self.tv_algorithm.setObjectName(u"tv_algorithm")

        self.gridLayout_3.addWidget(self.tv_algorithm, 0, 0, 1, 3)

        self.tabWidget.addTab(self.tab_Algorithm, "")

        self.gridLayout.addWidget(self.tabWidget, 1, 0, 1, 1)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setCenterButtons(False)

        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Algorithm Creator", None))
        self.l_NameAlgorithm.setText(QCoreApplication.translate("Dialog", u"Name of the algorithm", None))
        self.l_Version.setText(QCoreApplication.translate("Dialog", u"Version", None))
        self.l_Description.setText(QCoreApplication.translate("Dialog", u"Description of the algorithm", None))
        self.l_Author.setText(QCoreApplication.translate("Dialog", u"Author of the algorithm", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_Properties), QCoreApplication.translate("Dialog", u"Algorithm properties", None))
        self.b_AddBefore.setText("")
        self.b_MoveDown.setText("")
        self.b_Delete.setText("")
        self.b_MoveUp.setText("")
        self.b_AddAfter.setText("")
        self.b_Help.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_Algorithm), QCoreApplication.translate("Dialog", u"Algorithm steps", None))
    # retranslateUi

