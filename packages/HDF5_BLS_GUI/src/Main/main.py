from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QFileDialog, QGridLayout, QMainWindow, QMessageBox, QWidget

from configparser import ConfigParser
import pyperclip
from pathlib import Path

from .logic.hdf5_handler import HDF5Handler
from .widgets.log_widget import LogWidget
from .widgets.button_panel import ButtonPanel
from .widgets.architecture_widget import ArchitectureWidget
from .widgets.properties_widget import PropertiesWidget

from HDF5_BLS.errors import WrapperError_Overwrite, WrapperError_Save

class MainWindow(QMainWindow):

    def __init__(self):
        """Initializes the main window
        """
        super().__init__()

        self.gui_root = str(Path(__file__).resolve().parent.parent.parent)

        # Initializes the logic handler
        self.handler = HDF5Handler()

        # Load config file
        self.config = ConfigParser()
        self.config.read(self.gui_root+"/src/Main/config_Main.ini")

        # Set window title and geometry
        self.setWindowTitle(self.config['Default_contents']['title'])
        self.setGeometry(int(self.config['Geometry']['x']),
                         int(self.config['Geometry']['y']),
                         int(self.config['Geometry']['width']),
                         int(self.config['Geometry']['height']))

        # Create widgets
        self.button_panel = ButtonPanel(self.config, self.gui_root)
        self.architecture_widget = ArchitectureWidget(self.handler, self.config, self.gui_root)
        self.properties_widget = PropertiesWidget(self.handler, self.config)
        self.log_widget = LogWidget(self.config)
        
        # Shortcut for logging
        self.log = self.log_widget

        # Setup layout
        self._setup_layout()

        # Initialize menu bar
        self._initialize_menubar()

        # Connect signals
        self._connect_signals()

    def _setup_layout(self):
        self.main_layout = QGridLayout()
        self.main_layout.addWidget(self.button_panel, 1, 1, 1, 3)
        self.main_layout.addWidget(self.architecture_widget, 3, 1, 1, 1)
        self.main_layout.addWidget(self.properties_widget, 3, 3, 1, 1)
        self.main_layout.addWidget(self.log_widget, 5, 1, 1, 3)
        
        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

    def _connect_signals(self):
        # Button Panel signals
        self.button_panel.new_requested.connect(self.new_hdf5)
        self.button_panel.open_requested.connect(self.open_hdf5)
        self.button_panel.save_requested.connect(self.save_hdf5)
        self.button_panel.repack_requested.connect(self.repack)
        self.button_panel.add_requested.connect(self.add_data)
        self.button_panel.remove_requested.connect(self.remove_element)
        self.button_panel.close_requested.connect(self.close)

        # Architecture Widget signals
        self.architecture_widget.selection_changed.connect(self.properties_widget.update_properties)
        self.architecture_widget.delete_requested.connect(self.remove_element)
        self.architecture_widget.add_group_requested.connect(self.add_group)
        self.architecture_widget.files_dropped.connect(self.handle_file_drop)

    def _initialize_menubar(self):
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction(QIcon(f"{self.gui_root}/assets/img/new_db.svg"), "&New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_hdf5)
        file_menu.addAction(new_action)
        
        open_action = QAction(QIcon(f"{self.gui_root}/assets/img/open_db.svg"), "&Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_hdf5)
        file_menu.addAction(open_action)
        
        save_action = QAction(QIcon(f"{self.gui_root}/assets/img/save.svg"), "&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_hdf5)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")
        
        add_attr_action = QAction("Add Attribute", self)
        add_attr_action.triggered.connect(self.add_attribute)
        edit_menu.addAction(add_attr_action)
        
        remove_attr_action = QAction("Remove Attribute", self)
        remove_attr_action.triggered.connect(self.remove_attribute)
        edit_menu.addAction(remove_attr_action)

        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")
        
        export_attrs_action = QAction("Export Normalized Attributes", self)
        export_attrs_action.triggered.connect(self.export_normalized_attributes)
        tools_menu.addAction(export_attrs_action)

        # Help Menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction(QIcon(f"{self.gui_root}/assets/img/help.svg"), "&About", self)
        about_action.triggered.connect(lambda: QMessageBox.about(self, "About HDF5_BLS", "HDF5_BLS GUI\nVersion 1.0"))
        help_menu.addAction(about_action)

    @Slot()
    def closeEvent(self, event):
        """Close the window and exit the application.
        """
        if self.handler.wrp.save:
            if not self.handle_error_save():
                event.ignore()
                return
        
        self.handler.wrp.close(delete_temp_file = True)
        event.accept()

    def handle_error_save(self):
        """Function that handles the error when trying to close the wrapper without saving it. 
        """
        dialog = QMessageBox.question(self,"Unsaved changes", "The file has not been saved yet. Do you want to save it?", QMessageBox.Yes | QMessageBox.No |QMessageBox.Cancel)
        if dialog == QMessageBox.Yes:
            self.save_hdf5()
            self.handler.wrp.close()
        elif dialog == QMessageBox.No:
            self.handler.wrp.save = False
            self.handler.wrp.close()
        elif dialog == QMessageBox.Cancel:
            return False
        return True

    def new_hdf5(self):
        """Create a new HDF5 file.
        """
        if self.handler.wrp.save:
            if not self.handle_error_save():
                return
        
        self.handler.new_hdf5()
        self.architecture_widget.update_treeview()
        self.log.append(f"A new file has been created <b>Please save it to a non-temporary location</b>")

    @Slot()
    def open_hdf5(self, filepath = None):
        """Open an HDF5 file and update the UI.
        """
        if filepath is None or filepath == False:
            filepath = QFileDialog.getOpenFileName(self, "Open File", "", "HDF5 Files (*.h5)")[0]
            if not filepath: return

        if self.handler.wrp.save:
            if not self.handle_error_save():
                return
        
        self.handler.open_hdf5(filepath)
        self.architecture_widget.update_treeview()
        self.properties_widget.update_properties("Brillouin")
        self.log.append(f"<i>{filepath}</i> opened")

    def repack(self):
        """Repacks the wrapper to minimize its size.
        """
        self.handler.repack()
        self.log.append(f"The HDF5 file has been repacked")

    def save_hdf5(self):
        """Save the current data to an HDF5 file.
        """
        filepath = QFileDialog.getSaveFileName(self, "Save File", "", "HDF5 Files (*.h5)")[0]
        if filepath:
            try:
                self.handler.save_as_hdf5(filepath)
            except WrapperError_Overwrite:
                self.handler.save_as_hdf5(filepath, overwrite = True)
            self.log.append(f"<i>{filepath}</i> has been saved")

    def add_data(self):
        """Add a new element to the HDF5 file.
        """
        filepaths = QFileDialog.getOpenFileNames(self, "Select a file to add", "All files (*)")[0]
        if len(filepaths) == 0: return

        parent_path = self.architecture_widget.get_current_path()
        for filepath in filepaths:
            try:
                self.handler.import_data(filepath, parent_path)
                self.log.append(f"<i>{filepath}</i> imported to {parent_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not import {filepath}: {e}")
        
        self.architecture_widget.update_treeview()

    def handle_file_drop(self, filepaths, parent_path):
        """Handle files dropped on the architecture widget.
        """
        for filepath in filepaths:
            if filepath.lower().endswith(".h5"):
                self.open_hdf5(filepath)
            else:
                try:
                    self.handler.import_data(filepath, parent_path)
                    self.log.append(f"<i>{filepath}</i> imported to {parent_path}")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not import {filepath}: {e}")
        
        self.architecture_widget.update_treeview()
        self.log.append("Drag and drop operation completed")

    def add_group(self, path=None):
        """Add a new group to the HDF5 file.
        """
        if path is None:
            path = self.architecture_widget.get_current_path()
            
        try:
            # For simplicity, using a default name "New Group"
            self.handler.create_group("New Group", path)
            self.architecture_widget.update_treeview()
            self.log.append(f"Group created in <i>{path}</i>")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not create group: {e}")

    def add_attribute(self):
        """Add a new attribute to the selected element.
        """
        from .attribute_dialog import AddAttributeDialog
        dialog = AddAttributeDialog(self)
        if dialog.exec_():
            full_name, value = dialog.get_data()
            path = self.architecture_widget.get_current_path()
            if path:
                try:
                    self.handler.wrp.add_attributes(attributes={full_name: value}, parent_group=path)
                    self.properties_widget.update_properties(path)
                    self.log.append(f"Attribute <b>{full_name}</b> added to <i>{path}</i>")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not add attribute: {e}")

    def remove_element(self, path=None):
        """Remove the selected element from the HDF5 file.
        """
        if path is None:
            path = self.architecture_widget.get_current_path()

        if path == "Brillouin":
            QMessageBox.warning(self, "Warning", "You can't remove the root element")
            return
        
        dialog = QMessageBox.question(self, "Warning", f"Are you sure you want to remove <b>{path}</b>?")
        if dialog == QMessageBox.Yes:
            try:
                self.handler.remove_element(path)
                self.architecture_widget.update_treeview()
                self.log.append(f"Element <i>{path}</i> removed")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not remove element: {e}")

    def remove_attribute(self):
        """Remove an attribute from the selected element.
        """
        QMessageBox.information(self, "Not implemented", "Remove attribute functionality is not yet implemented.")

    def export_normalized_attributes(self):
        """Export the normalized list of attributes to an Excel file.
        """
        from HDF5_BLS import NormalizedAttributes
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Normalized Attributes", str(Path.home() / "normalized_attributes.xlsx"), "Excel Files (*.xlsx)")
        if filepath:
            try:
                NormalizedAttributes.to_excel(filepath)
                self.log.append(f"Normalized attributes exported to <i>{filepath}</i>")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not export normalized attributes: {e}")

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())