# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QGroupBox, QHeaderView,
    QMainWindow, QMenu, QMenuBar, QPushButton,
    QSizePolicy, QSpacerItem, QStatusBar, QTabWidget,
    QTableView, QTextBrowser, QTreeView, QWidget)
import Icons_rc

class Ui_w_Main(object):
    def setupUi(self, w_Main):
        if not w_Main.objectName():
            w_Main.setObjectName(u"w_Main")
        w_Main.resize(850, 600)
        self.a_OpenHDF5 = QAction(w_Main)
        self.a_OpenHDF5.setObjectName(u"a_OpenHDF5")
        self.a_Save = QAction(w_Main)
        self.a_Save.setObjectName(u"a_Save")
        self.a_ImportCSV = QAction(w_Main)
        self.a_ImportCSV.setObjectName(u"a_ImportCSV")
        self.a_NewHDF5 = QAction(w_Main)
        self.a_NewHDF5.setObjectName(u"a_NewHDF5")
        self.a_AddData = QAction(w_Main)
        self.a_AddData.setObjectName(u"a_AddData")
        self.a_ConvertCSV = QAction(w_Main)
        self.a_ConvertCSV.setObjectName(u"a_ConvertCSV")
        self.a_ConvertCSV.setEnabled(False)
        self.a_Close = QAction(w_Main)
        self.a_Close.setObjectName(u"a_Close")
        self.a_SaveFileAs = QAction(w_Main)
        self.a_SaveFileAs.setObjectName(u"a_SaveFileAs")
        self.a_RepackHDF5 = QAction(w_Main)
        self.a_RepackHDF5.setObjectName(u"a_RepackHDF5")
        self.a_RepackHDF5.setEnabled(False)
        self.a_RenameElement = QAction(w_Main)
        self.a_RenameElement.setObjectName(u"a_RenameElement")
        self.a_RenameElement.setEnabled(False)
        self.a_ExportPython = QAction(w_Main)
        self.a_ExportPython.setObjectName(u"a_ExportPython")
        self.actionGet_PSD = QAction(w_Main)
        self.actionGet_PSD.setObjectName(u"actionGet_PSD")
        self.actionApply_Treatment = QAction(w_Main)
        self.actionApply_Treatment.setObjectName(u"actionApply_Treatment")
        self.centralwidget = QWidget(w_Main)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gb_viewers = QGroupBox(self.centralwidget)
        self.gb_viewers.setObjectName(u"gb_viewers")
        self.gridLayout_3 = QGridLayout(self.gb_viewers)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.treeView = QTreeView(self.gb_viewers)
        self.treeView.setObjectName(u"treeView")

        self.gridLayout_3.addWidget(self.treeView, 0, 0, 1, 1)

        self.tabWidget = QTabWidget(self.gb_viewers)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab_Measure = QWidget()
        self.tab_Measure.setObjectName(u"tab_Measure")
        self.gridLayout_5 = QGridLayout(self.tab_Measure)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.b_AddPropertyMeasure = QPushButton(self.tab_Measure)
        self.b_AddPropertyMeasure.setObjectName(u"b_AddPropertyMeasure")
        self.b_AddPropertyMeasure.setEnabled(False)
        icon = QIcon()
        icon.addFile(u":/Buttons/icon/add_spectra.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.b_AddPropertyMeasure.setIcon(icon)
        self.b_AddPropertyMeasure.setIconSize(QSize(20, 20))

        self.gridLayout_5.addWidget(self.b_AddPropertyMeasure, 1, 1, 1, 1)

        self.b_RemovePropertyMeasure = QPushButton(self.tab_Measure)
        self.b_RemovePropertyMeasure.setObjectName(u"b_RemovePropertyMeasure")
        self.b_RemovePropertyMeasure.setEnabled(False)
        icon1 = QIcon()
        icon1.addFile(u":/Buttons/icon/remove_spectra.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.b_RemovePropertyMeasure.setIcon(icon1)
        self.b_RemovePropertyMeasure.setIconSize(QSize(20, 20))

        self.gridLayout_5.addWidget(self.b_RemovePropertyMeasure, 1, 2, 1, 1)

        self.b_LoadPropertiesMeasure = QPushButton(self.tab_Measure)
        self.b_LoadPropertiesMeasure.setObjectName(u"b_LoadPropertiesMeasure")
        self.b_LoadPropertiesMeasure.setEnabled(False)
        icon2 = QIcon()
        icon2.addFile(u":/Buttons/icon/open_config.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.b_LoadPropertiesMeasure.setIcon(icon2)
        self.b_LoadPropertiesMeasure.setIconSize(QSize(20, 20))

        self.gridLayout_5.addWidget(self.b_LoadPropertiesMeasure, 1, 0, 1, 1)

        self.tableView_Measure = QTableView(self.tab_Measure)
        self.tableView_Measure.setObjectName(u"tableView_Measure")

        self.gridLayout_5.addWidget(self.tableView_Measure, 0, 0, 1, 3)

        self.tabWidget.addTab(self.tab_Measure, "")
        self.tab_Spectrometer = QWidget()
        self.tab_Spectrometer.setObjectName(u"tab_Spectrometer")
        self.gridLayout_4 = QGridLayout(self.tab_Spectrometer)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.b_AddPropertySpectrometer = QPushButton(self.tab_Spectrometer)
        self.b_AddPropertySpectrometer.setObjectName(u"b_AddPropertySpectrometer")
        self.b_AddPropertySpectrometer.setEnabled(False)
        self.b_AddPropertySpectrometer.setIcon(icon)
        self.b_AddPropertySpectrometer.setIconSize(QSize(20, 20))

        self.gridLayout_4.addWidget(self.b_AddPropertySpectrometer, 1, 1, 1, 1)

        self.b_RemovePropertySpectrometer = QPushButton(self.tab_Spectrometer)
        self.b_RemovePropertySpectrometer.setObjectName(u"b_RemovePropertySpectrometer")
        self.b_RemovePropertySpectrometer.setEnabled(False)
        self.b_RemovePropertySpectrometer.setIcon(icon1)
        self.b_RemovePropertySpectrometer.setIconSize(QSize(20, 20))

        self.gridLayout_4.addWidget(self.b_RemovePropertySpectrometer, 1, 2, 1, 1)

        self.b_LoadPropertiesSpectrometer = QPushButton(self.tab_Spectrometer)
        self.b_LoadPropertiesSpectrometer.setObjectName(u"b_LoadPropertiesSpectrometer")
        self.b_LoadPropertiesSpectrometer.setEnabled(False)
        self.b_LoadPropertiesSpectrometer.setIcon(icon2)
        self.b_LoadPropertiesSpectrometer.setIconSize(QSize(20, 20))

        self.gridLayout_4.addWidget(self.b_LoadPropertiesSpectrometer, 1, 0, 1, 1)

        self.tableView_Spectrometer = QTableView(self.tab_Spectrometer)
        self.tableView_Spectrometer.setObjectName(u"tableView_Spectrometer")

        self.gridLayout_4.addWidget(self.tableView_Spectrometer, 0, 0, 1, 3)

        self.tabWidget.addTab(self.tab_Spectrometer, "")

        self.gridLayout_3.addWidget(self.tabWidget, 0, 1, 1, 1)


        self.gridLayout.addWidget(self.gb_viewers, 1, 0, 1, 1)

        self.gb_buttons = QGroupBox(self.centralwidget)
        self.gb_buttons.setObjectName(u"gb_buttons")
        self.gridLayout_2 = QGridLayout(self.gb_buttons)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.b_ConvertCSV = QPushButton(self.gb_buttons)
        self.b_ConvertCSV.setObjectName(u"b_ConvertCSV")
        self.b_ConvertCSV.setEnabled(False)
        icon3 = QIcon()
        icon3.addFile(u":/Buttons/icon/properties_to_csv.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.b_ConvertCSV.setIcon(icon3)
        self.b_ConvertCSV.setIconSize(QSize(35, 35))

        self.gridLayout_2.addWidget(self.b_ConvertCSV, 0, 6, 1, 1)

        self.b_Save = QPushButton(self.gb_buttons)
        self.b_Save.setObjectName(u"b_Save")
        self.b_Save.setEnabled(True)
        icon4 = QIcon()
        icon4.addFile(u":/Buttons/icon/save.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.b_Save.setIcon(icon4)
        self.b_Save.setIconSize(QSize(35, 35))

        self.gridLayout_2.addWidget(self.b_Save, 0, 2, 1, 1)

        self.b_AddData = QPushButton(self.gb_buttons)
        self.b_AddData.setObjectName(u"b_AddData")
        self.b_AddData.setEnabled(False)
        self.b_AddData.setIcon(icon)
        self.b_AddData.setIconSize(QSize(35, 35))

        self.gridLayout_2.addWidget(self.b_AddData, 0, 3, 1, 1)

        self.b_NewHDF5 = QPushButton(self.gb_buttons)
        self.b_NewHDF5.setObjectName(u"b_NewHDF5")
        icon5 = QIcon()
        icon5.addFile(u":/Buttons/icon/new_db.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.b_NewHDF5.setIcon(icon5)
        self.b_NewHDF5.setIconSize(QSize(35, 35))

        self.gridLayout_2.addWidget(self.b_NewHDF5, 0, 0, 1, 1)

        self.b_RemoveData = QPushButton(self.gb_buttons)
        self.b_RemoveData.setObjectName(u"b_RemoveData")
        self.b_RemoveData.setEnabled(False)
        self.b_RemoveData.setIcon(icon1)
        self.b_RemoveData.setIconSize(QSize(35, 35))

        self.gridLayout_2.addWidget(self.b_RemoveData, 0, 4, 1, 1)

        self.b_Close = QPushButton(self.gb_buttons)
        self.b_Close.setObjectName(u"b_Close")
        icon6 = QIcon()
        icon6.addFile(u":/Buttons/icon/exit.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.b_Close.setIcon(icon6)
        self.b_Close.setIconSize(QSize(35, 35))

        self.gridLayout_2.addWidget(self.b_Close, 0, 8, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer, 0, 7, 1, 1)

        self.b_OpenHDF5 = QPushButton(self.gb_buttons)
        self.b_OpenHDF5.setObjectName(u"b_OpenHDF5")
        icon7 = QIcon()
        icon7.addFile(u":/Buttons/icon/open_db.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.b_OpenHDF5.setIcon(icon7)
        self.b_OpenHDF5.setIconSize(QSize(35, 35))

        self.gridLayout_2.addWidget(self.b_OpenHDF5, 0, 1, 1, 1)

        self.b_ExportCodeLine = QPushButton(self.gb_buttons)
        self.b_ExportCodeLine.setObjectName(u"b_ExportCodeLine")
        self.b_ExportCodeLine.setEnabled(False)
        icon8 = QIcon()
        icon8.addFile(u":/Buttons/icon/export_code.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.b_ExportCodeLine.setIcon(icon8)
        self.b_ExportCodeLine.setIconSize(QSize(35, 35))

        self.gridLayout_2.addWidget(self.b_ExportCodeLine, 0, 5, 1, 1)


        self.gridLayout.addWidget(self.gb_buttons, 0, 0, 1, 1)

        self.textBrowser_Log = QTextBrowser(self.centralwidget)
        self.textBrowser_Log.setObjectName(u"textBrowser_Log")
        self.textBrowser_Log.setMaximumSize(QSize(16777215, 100))

        self.gridLayout.addWidget(self.textBrowser_Log, 2, 0, 1, 1)

        w_Main.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(w_Main)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 850, 37))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuEdit = QMenu(self.menubar)
        self.menuEdit.setObjectName(u"menuEdit")
        self.menuExport_code = QMenu(self.menuEdit)
        self.menuExport_code.setObjectName(u"menuExport_code")
        self.menuExport_code.setEnabled(False)
        w_Main.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(w_Main)
        self.statusbar.setObjectName(u"statusbar")
        w_Main.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menuFile.addAction(self.a_NewHDF5)
        self.menuFile.addAction(self.a_OpenHDF5)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.a_Save)
        self.menuFile.addAction(self.a_SaveFileAs)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.a_AddData)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.a_Close)
        self.menuEdit.addAction(self.a_RepackHDF5)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.a_ImportCSV)
        self.menuEdit.addAction(self.a_ConvertCSV)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.a_RenameElement)
        self.menuEdit.addAction(self.menuExport_code.menuAction())
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionGet_PSD)
        self.menuEdit.addAction(self.actionApply_Treatment)
        self.menuExport_code.addAction(self.a_ExportPython)

        self.retranslateUi(w_Main)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(w_Main)
    # setupUi

    def retranslateUi(self, w_Main):
        w_Main.setWindowTitle(QCoreApplication.translate("w_Main", u"HDF5 BLS GUI", None))
        self.a_OpenHDF5.setText(QCoreApplication.translate("w_Main", u"Open HDF5 file", None))
        self.a_Save.setText(QCoreApplication.translate("w_Main", u"Save file", None))
        self.a_ImportCSV.setText(QCoreApplication.translate("w_Main", u"Import Properties from CSV", None))
        self.a_NewHDF5.setText(QCoreApplication.translate("w_Main", u"New HDF5 file", None))
        self.a_AddData.setText(QCoreApplication.translate("w_Main", u"Add Raw file", None))
        self.a_ConvertCSV.setText(QCoreApplication.translate("w_Main", u"Export Properties to CSV", None))
        self.a_Close.setText(QCoreApplication.translate("w_Main", u"Close", None))
        self.a_SaveFileAs.setText(QCoreApplication.translate("w_Main", u"Save file as", None))
        self.a_RepackHDF5.setText(QCoreApplication.translate("w_Main", u"Repack HDF5", None))
        self.a_RenameElement.setText(QCoreApplication.translate("w_Main", u"Rename element", None))
        self.a_ExportPython.setText(QCoreApplication.translate("w_Main", u"Python", None))
        self.actionGet_PSD.setText(QCoreApplication.translate("w_Main", u"Get PSD", None))
        self.actionApply_Treatment.setText(QCoreApplication.translate("w_Main", u"Apply Treatment", None))
        self.gb_viewers.setTitle("")
        self.b_AddPropertyMeasure.setText("")
        self.b_RemovePropertyMeasure.setText("")
        self.b_LoadPropertiesMeasure.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_Measure), QCoreApplication.translate("w_Main", u"Tab 1", None))
        self.b_AddPropertySpectrometer.setText("")
        self.b_RemovePropertySpectrometer.setText("")
        self.b_LoadPropertiesSpectrometer.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_Spectrometer), QCoreApplication.translate("w_Main", u"Tab 2", None))
        self.gb_buttons.setTitle("")
        self.b_ConvertCSV.setText("")
        self.b_Save.setText("")
        self.b_AddData.setText("")
        self.b_NewHDF5.setText("")
        self.b_RemoveData.setText("")
        self.b_Close.setText("")
        self.b_OpenHDF5.setText("")
        self.b_ExportCodeLine.setText("")
        self.menuFile.setTitle(QCoreApplication.translate("w_Main", u"File", None))
        self.menuEdit.setTitle(QCoreApplication.translate("w_Main", u"Actions", None))
        self.menuExport_code.setTitle(QCoreApplication.translate("w_Main", u"Export code", None))
    # retranslateUi

