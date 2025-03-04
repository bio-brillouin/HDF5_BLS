# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'parameters_curve.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFrame, QGridLayout, QPushButton,
    QSizePolicy, QSpacerItem, QWidget)
import Icons_rc

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(795, 580)
        self.gridLayout = QGridLayout(Dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.frame = QFrame(Dialog)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_3 = QGridLayout(self.frame)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.cb_curves = QComboBox(self.frame)
        self.cb_curves.setObjectName(u"cb_curves")

        self.gridLayout_3.addWidget(self.cb_curves, 0, 0, 1, 1)

        self.frame_graph = QFrame(self.frame)
        self.frame_graph.setObjectName(u"frame_graph")
        self.frame_graph.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_graph.setFrameShadow(QFrame.Shadow.Raised)

        self.gridLayout_3.addWidget(self.frame_graph, 1, 0, 1, 1)


        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)

        self.frame_parameters = QFrame(Dialog)
        self.frame_parameters.setObjectName(u"frame_parameters")
        self.frame_parameters.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_parameters.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_2 = QGridLayout(self.frame_parameters)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.b_helpFunction = QPushButton(self.frame_parameters)
        self.b_helpFunction.setObjectName(u"b_helpFunction")
        self.b_helpFunction.setEnabled(True)
        icon = QIcon()
        icon.addFile(u":/Buttons/icon/help.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.b_helpFunction.setIcon(icon)
        self.b_helpFunction.setIconSize(QSize(20, 20))
        self.b_helpFunction.setCheckable(False)

        self.gridLayout_2.addWidget(self.b_helpFunction, 0, 1, 1, 1)

        self.frame_confirmParam = QFrame(self.frame_parameters)
        self.frame_confirmParam.setObjectName(u"frame_confirmParam")
        self.frame_confirmParam.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_confirmParam.setFrameShadow(QFrame.Shadow.Raised)

        self.gridLayout_2.addWidget(self.frame_confirmParam, 3, 0, 1, 2)

        self.frame_paramVar = QFrame(self.frame_parameters)
        self.frame_paramVar.setObjectName(u"frame_paramVar")
        self.frame_paramVar.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_paramVar.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_4 = QGridLayout(self.frame_paramVar)
        self.gridLayout_4.setObjectName(u"gridLayout_4")

        self.gridLayout_2.addWidget(self.frame_paramVar, 1, 0, 1, 2)

        self.cb_functions = QComboBox(self.frame_parameters)
        self.cb_functions.setObjectName(u"cb_functions")

        self.gridLayout_2.addWidget(self.cb_functions, 0, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer, 2, 0, 1, 1)


        self.gridLayout.addWidget(self.frame_parameters, 0, 1, 1, 1)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 2)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.b_helpFunction.setText("")
    # retranslateUi

