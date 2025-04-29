# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'analyze_window.ui'
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
    QFrame, QGridLayout, QHeaderView, QLabel,
    QPushButton, QSizePolicy, QTreeWidget, QTreeWidgetItem,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(900, 600)
        self.gridLayout = QGridLayout(Dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.f_Right = QFrame(Dialog)
        self.f_Right.setObjectName(u"f_Right")
        self.f_Right.setFrameShape(QFrame.Shape.StyledPanel)
        self.f_Right.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_3 = QGridLayout(self.f_Right)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.b_OpenAlgorithm = QPushButton(self.f_Right)
        self.b_OpenAlgorithm.setObjectName(u"b_OpenAlgorithm")

        self.gridLayout_3.addWidget(self.b_OpenAlgorithm, 2, 0, 1, 1)

        self.l_titleAlgorithm = QLabel(self.f_Right)
        self.l_titleAlgorithm.setObjectName(u"l_titleAlgorithm")
        font = QFont()
        font.setBold(True)
        self.l_titleAlgorithm.setFont(font)
        self.l_titleAlgorithm.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_3.addWidget(self.l_titleAlgorithm, 0, 0, 1, 2)

        self.f_Functions = QFrame(self.f_Right)
        self.f_Functions.setObjectName(u"f_Functions")
        self.f_Functions.setFrameShape(QFrame.Shape.StyledPanel)
        self.f_Functions.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_4 = QGridLayout(self.f_Functions)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.b_SaveAlgorithm = QPushButton(self.f_Functions)
        self.b_SaveAlgorithm.setObjectName(u"b_SaveAlgorithm")

        self.gridLayout_4.addWidget(self.b_SaveAlgorithm, 1, 0, 1, 1)

        self.t_Functions = QTreeWidget(self.f_Functions)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"1");
        self.t_Functions.setHeaderItem(__qtreewidgetitem)
        self.t_Functions.setObjectName(u"t_Functions")

        self.gridLayout_4.addWidget(self.t_Functions, 0, 0, 1, 2)

        self.b_RunAll = QPushButton(self.f_Functions)
        self.b_RunAll.setObjectName(u"b_RunAll")

        self.gridLayout_4.addWidget(self.b_RunAll, 1, 1, 1, 1)


        self.gridLayout_3.addWidget(self.f_Functions, 3, 0, 1, 2)

        self.b_GraphAlgorithm = QPushButton(self.f_Right)
        self.b_GraphAlgorithm.setObjectName(u"b_GraphAlgorithm")

        self.gridLayout_3.addWidget(self.b_GraphAlgorithm, 1, 0, 1, 2)

        self.b_NewAlgorithm = QPushButton(self.f_Right)
        self.b_NewAlgorithm.setObjectName(u"b_NewAlgorithm")

        self.gridLayout_3.addWidget(self.b_NewAlgorithm, 2, 1, 1, 1)


        self.gridLayout.addWidget(self.f_Right, 0, 1, 1, 1)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 2)

        self.f_left = QFrame(Dialog)
        self.f_left.setObjectName(u"f_left")
        self.f_left.setFrameShape(QFrame.Shape.StyledPanel)
        self.f_left.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_2 = QGridLayout(self.f_left)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.f_PlotSelect = QFrame(self.f_left)
        self.f_PlotSelect.setObjectName(u"f_PlotSelect")
        self.f_PlotSelect.setFrameShape(QFrame.Shape.StyledPanel)
        self.f_PlotSelect.setFrameShadow(QFrame.Shadow.Raised)

        self.gridLayout_2.addWidget(self.f_PlotSelect, 3, 0, 1, 2)

        self.f_Dimension = QFrame(self.f_left)
        self.f_Dimension.setObjectName(u"f_Dimension")
        self.f_Dimension.setFrameShape(QFrame.Shape.StyledPanel)
        self.f_Dimension.setFrameShadow(QFrame.Shadow.Raised)

        self.gridLayout_2.addWidget(self.f_Dimension, 1, 0, 1, 2)

        self.frame_graph = QFrame(self.f_left)
        self.frame_graph.setObjectName(u"frame_graph")
        self.frame_graph.setMinimumSize(QSize(500, 350))
        self.frame_graph.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_graph.setFrameShadow(QFrame.Shadow.Raised)

        self.gridLayout_2.addWidget(self.frame_graph, 2, 0, 1, 2)

        self.b_Sum = QPushButton(self.f_left)
        self.b_Sum.setObjectName(u"b_Sum")

        self.gridLayout_2.addWidget(self.b_Sum, 0, 0, 1, 2)


        self.gridLayout.addWidget(self.f_left, 0, 0, 1, 1)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Analyze window", None))
        self.b_OpenAlgorithm.setText(QCoreApplication.translate("Dialog", u"Open Algorithm", None))
        self.l_titleAlgorithm.setText(QCoreApplication.translate("Dialog", u"Blank algorithm", None))
        self.b_SaveAlgorithm.setText(QCoreApplication.translate("Dialog", u"Save Algorithm", None))
        self.b_RunAll.setText(QCoreApplication.translate("Dialog", u"Run all", None))
        self.b_GraphAlgorithm.setText(QCoreApplication.translate("Dialog", u"Display Algorithm Graph", None))
        self.b_NewAlgorithm.setText(QCoreApplication.translate("Dialog", u"New Algorithm", None))
        self.b_Sum.setText(QCoreApplication.translate("Dialog", u"Plot average", None))
    # retranslateUi

