# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'export_image.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QFrame, QGridLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QTabWidget, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(600, 400)
        self.gridLayout = QGridLayout(Dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)

        self.le_labely = QTabWidget(Dialog)
        self.le_labely.setObjectName(u"le_labely")
        self.tab_FileProperties = QWidget()
        self.tab_FileProperties.setObjectName(u"tab_FileProperties")
        self.gridLayout_2 = QGridLayout(self.tab_FileProperties)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.l_Filepath = QLabel(self.tab_FileProperties)
        self.l_Filepath.setObjectName(u"l_Filepath")

        self.gridLayout_2.addWidget(self.l_Filepath, 0, 0, 1, 1)

        self.pushButton = QPushButton(self.tab_FileProperties)
        self.pushButton.setObjectName(u"pushButton")

        self.gridLayout_2.addWidget(self.pushButton, 0, 1, 1, 1)

        self.l_ExportFormat = QLabel(self.tab_FileProperties)
        self.l_ExportFormat.setObjectName(u"l_ExportFormat")

        self.gridLayout_2.addWidget(self.l_ExportFormat, 2, 0, 1, 1)

        self.cb_ExportFormat = QComboBox(self.tab_FileProperties)
        self.cb_ExportFormat.setObjectName(u"cb_ExportFormat")

        self.gridLayout_2.addWidget(self.cb_ExportFormat, 2, 1, 1, 1)

        self.cBox_Hierarchy = QCheckBox(self.tab_FileProperties)
        self.cBox_Hierarchy.setObjectName(u"cBox_Hierarchy")

        self.gridLayout_2.addWidget(self.cBox_Hierarchy, 1, 0, 1, 2)

        self.le_labely.addTab(self.tab_FileProperties, "")
        self.tab_ImageProperties = QWidget()
        self.tab_ImageProperties.setObjectName(u"tab_ImageProperties")
        self.gridLayout_3 = QGridLayout(self.tab_ImageProperties)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.l_labelx = QLabel(self.tab_ImageProperties)
        self.l_labelx.setObjectName(u"l_labelx")

        self.gridLayout_3.addWidget(self.l_labelx, 6, 0, 1, 1)

        self.l_Colormap = QLabel(self.tab_ImageProperties)
        self.l_Colormap.setObjectName(u"l_Colormap")

        self.gridLayout_3.addWidget(self.l_Colormap, 3, 0, 1, 1)

        self.lineEdit_3 = QLineEdit(self.tab_ImageProperties)
        self.lineEdit_3.setObjectName(u"lineEdit_3")

        self.gridLayout_3.addWidget(self.lineEdit_3, 7, 1, 1, 1)

        self.cb_Axis = QCheckBox(self.tab_ImageProperties)
        self.cb_Axis.setObjectName(u"cb_Axis")

        self.gridLayout_3.addWidget(self.cb_Axis, 5, 0, 1, 1)

        self.cb_SimpleImage = QCheckBox(self.tab_ImageProperties)
        self.cb_SimpleImage.setObjectName(u"cb_SimpleImage")

        self.gridLayout_3.addWidget(self.cb_SimpleImage, 0, 0, 1, 2)

        self.le_labelx = QLineEdit(self.tab_ImageProperties)
        self.le_labelx.setObjectName(u"le_labelx")

        self.gridLayout_3.addWidget(self.le_labelx, 6, 1, 1, 1)

        self.lineEdit = QLineEdit(self.tab_ImageProperties)
        self.lineEdit.setObjectName(u"lineEdit")

        self.gridLayout_3.addWidget(self.lineEdit, 1, 1, 1, 1)

        self.cb_Colorbar = QCheckBox(self.tab_ImageProperties)
        self.cb_Colorbar.setObjectName(u"cb_Colorbar")

        self.gridLayout_3.addWidget(self.cb_Colorbar, 2, 0, 1, 2)

        self.l_FigSize = QLabel(self.tab_ImageProperties)
        self.l_FigSize.setObjectName(u"l_FigSize")

        self.gridLayout_3.addWidget(self.l_FigSize, 1, 0, 1, 1)

        self.cb_Colormap = QComboBox(self.tab_ImageProperties)
        self.cb_Colormap.setObjectName(u"cb_Colormap")

        self.gridLayout_3.addWidget(self.cb_Colormap, 3, 1, 1, 1)

        self.l_labely = QLabel(self.tab_ImageProperties)
        self.l_labely.setObjectName(u"l_labely")

        self.gridLayout_3.addWidget(self.l_labely, 7, 0, 1, 1)

        self.cb_Scalebar = QCheckBox(self.tab_ImageProperties)
        self.cb_Scalebar.setObjectName(u"cb_Scalebar")

        self.gridLayout_3.addWidget(self.cb_Scalebar, 4, 0, 1, 1)

        self.le_labely.addTab(self.tab_ImageProperties, "")
        self.tab_Visualizer = QWidget()
        self.tab_Visualizer.setObjectName(u"tab_Visualizer")
        self.gridLayout_4 = QGridLayout(self.tab_Visualizer)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.cb_ImageChoice = QComboBox(self.tab_Visualizer)
        self.cb_ImageChoice.setObjectName(u"cb_ImageChoice")

        self.gridLayout_4.addWidget(self.cb_ImageChoice, 0, 0, 1, 1)

        self.f_Image = QFrame(self.tab_Visualizer)
        self.f_Image.setObjectName(u"f_Image")
        self.f_Image.setFrameShape(QFrame.Shape.StyledPanel)
        self.f_Image.setFrameShadow(QFrame.Shadow.Raised)

        self.gridLayout_4.addWidget(self.f_Image, 1, 0, 1, 1)

        self.le_labely.addTab(self.tab_Visualizer, "")

        self.gridLayout.addWidget(self.le_labely, 0, 0, 1, 1)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        self.le_labely.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.l_Filepath.setText(QCoreApplication.translate("Dialog", u"TextLabel", None))
        self.pushButton.setText(QCoreApplication.translate("Dialog", u"Change Parent directory", None))
        self.l_ExportFormat.setText(QCoreApplication.translate("Dialog", u"Export Format", None))
        self.cBox_Hierarchy.setText(QCoreApplication.translate("Dialog", u"Keep Hierarchy", None))
        self.le_labely.setTabText(self.le_labely.indexOf(self.tab_FileProperties), QCoreApplication.translate("Dialog", u"File Properties", None))
        self.l_labelx.setText(QCoreApplication.translate("Dialog", u"Label x", None))
        self.l_Colormap.setText(QCoreApplication.translate("Dialog", u"Set Colormap", None))
        self.cb_Axis.setText(QCoreApplication.translate("Dialog", u"Use axises", None))
        self.cb_SimpleImage.setText(QCoreApplication.translate("Dialog", u"Export simple image", None))
        self.cb_Colorbar.setText(QCoreApplication.translate("Dialog", u"Add Colorbar", None))
        self.l_FigSize.setText(QCoreApplication.translate("Dialog", u"Figure size (mm)", None))
        self.l_labely.setText(QCoreApplication.translate("Dialog", u"Label y", None))
        self.cb_Scalebar.setText(QCoreApplication.translate("Dialog", u"Use scalebar", None))
        self.le_labely.setTabText(self.le_labely.indexOf(self.tab_ImageProperties), QCoreApplication.translate("Dialog", u"Image Properties", None))
        self.le_labely.setTabText(self.le_labely.indexOf(self.tab_Visualizer), QCoreApplication.translate("Dialog", u"Preview", None))
    # retranslateUi

