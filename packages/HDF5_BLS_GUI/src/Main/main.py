from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QFileDialog, QGridLayout, QMainWindow, QMessageBox, QWidget, QInputDialog

from configparser import ConfigParser
import pyperclip
from pathlib import Path

from .logic.hdf5_handler import HDF5Handler
from .widgets.log_widget import LogWidget
from .widgets.button_panel import ButtonPanel
from .widgets.architecture_widget import ArchitectureWidget
from .widgets.properties_widget import PropertiesWidget
from treat_wizard.main import TreatWizard

from HDF5_BLS.errors import WrapperError_Overwrite, WrapperError_Save
from HDF5_BLS.load_formats import load_errors

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
        self.architecture_widget.add_group_requested.connect(self.add_group)
        self.architecture_widget.analyze_raw_data_requested.connect(self.analyze_raw_data)
        self.architecture_widget.change_type_requested.connect(self.change_brillouin_type)
        self.architecture_widget.delete_requested.connect(self.remove_element)
        self.architecture_widget.export_group_requested.connect(self.export_group)
        self.architecture_widget.export_path_clipboard.connect(self.handler.export_path_clipboard)
        self.architecture_widget.files_dropped.connect(self.handle_file_addition)
        self.architecture_widget.rename_requested.connect(self.rename_element)
        self.architecture_widget.selection_changed.connect(self.properties_widget.update_properties)
        self.architecture_widget.treat_PSD_requested.connect(self.treat_PSD)
        self.architecture_widget.update_property_requested.connect(self.properties_widget.update_properties)

        # Properties Widget signals
        self.properties_widget.edit_attributes_requested.connect(self.edit_attributes)

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
        
        edit_attr_action = QAction("Edit Attribute", self)
        edit_attr_action.triggered.connect(self.edit_attributes)
        edit_menu.addAction(edit_attr_action)
        
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

    def add_data(self):
        """Add a new element to the HDF5 file.
        """
        filepaths = QFileDialog.getOpenFileNames(self, "Select a file to add", "All files (*)")[0]
        if len(filepaths) == 0: return

        parent_path = self.architecture_widget.get_current_path()

        self.handle_file_addition(filepaths, parent_path)

    def add_group(self, path=None):
        """Add a new group to the HDF5 file.
        """
        if path is None:
            path = self.architecture_widget.get_current_path()
            
        try:
            # For simplicity, using a default name "New Group"
            self.handler.create_group("New Group", path)
            self.architecture_widget.update_treeview()
            new_path = f"{path}/New Group"
            self.architecture_widget.expand_path(new_path)
            self.architecture_widget.edit_path(new_path)
            self.log.append(f"Group <i>New Group</i> created in <i>{path}</i>")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not create group: {e}")

    def analyze_raw_data(self, path = None):
        """Analyze the raw data.
        """
        QMessageBox.information(self, "Not implemented", f"Raw data analysis functionality is not yet implemented. <b>{path}</b>")

    def change_brillouin_type(self, path, new_type):
        """Change the Brillouin type of the Brillouin group.
        """
        try:
            self.handler.wrp.change_brillouin_type(path, new_type)
            self.log.append(f"Brillouin type changed to <i>{new_type}</i> in <i>{path}</i>")
            self.architecture_widget.update_icon(path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not change Brillouin type: {e}")

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

    def edit_attributes(self, path = None):
        """Edit the attributes of the selected element.
        """
        print("\nEntering edit_attributes")
        if type(path) == type(None):
            path = self.architecture_widget.get_current_path()
            print("\npath - ", path)
        if path is False:
            path = 'Brillouin'

        from .attribute_edit_dialog import AttributeEditDialog
        dialog = AttributeEditDialog(self.handler, path, self)
        if dialog.exec():
            new_attrs = dialog.get_attributes()
            try:
                # Update attributes in HDF5
                self.handler.add_attributes(path, new_attrs, overwrite=True)
                self.properties_widget.update_properties(path)
                self.log.append(f"Attributes updated for <i>{path}</i>")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not update attributes: {e}")

    def export_group(self, path):
        """Export the group to an HDF5 file.
        """
        name_group = path.split("/")[-1]
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Group", str(Path.home() / f"{name_group}.h5"), "HDF5 Files (*.h5)")
        if filepath:
            try:
                self.handler.wrp.export_group(path, filepath)
                self.log.append(f"Group <i>{name_group}</i> exported to <i>{filepath}</i>")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not export group: {e}")

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

    def handle_file_addition(self, filepaths, parent_path, creator = None):
        """Handle files dropped on the architecture widget.

        Parameters:
        -----------
        filepaths : list
            List of file paths to import.
        parent_path : str
            Path to the parent group in the HDF5 file.
        creator : str, optional
            Creator of the data. Defaults to None.
        """
        # if filepaths is one or a list of directories
        is_dir = Path(filepaths[0]).is_dir()
        for path in filepaths:
            if not Path(path).is_dir() and is_dir:
                QMessageBox.warning(self, "Error", "All filepaths must have the same extension.")
                return
        
        if is_dir:
            # List all the file extensions recursively in the selected directories
            extensions = []
            for path in filepaths:
                extensions.extend([filepath.suffix for filepath in Path(path).rglob('*') if filepath.is_file()])
            extensions = list(set(extensions))
            try:
                extensions.remove("")
            except ValueError:
                pass
            
            # Ask the user to select between the file extensions with a tickable combo box
            extension, ok = QInputDialog.getItem(self, "Select Extension", "Please select the file extension:", extensions, 0, False)
            if ok and extension:
                pass
            else:
                return
            
            # Get the creator by trying to import the first element
            def get_creator(directories, extension):
                for path in directories:
                    for element in Path(path).rglob('*'):
                        if element.suffix == extension:
                            try:
                                self.handler.import_raw_data(str(element), parent_path)
                                self.handler.delete_element(parent_path + "/" + element.name.split(".")[0])
                            except load_errors.LoadError_creator as e:
                                creator, ok = QInputDialog.getItem(self, "Select Creator", f"Multiple creators found. Please select one:", e.creators, 0, False)
                                if ok and creator:
                                    self.handler.delete_element(parent_path + "/" + element.name.split(".")[0])
                                    return creator
                            return None
                        elif element.is_dir():
                            creator = add_element([element], extension)
                            if creator:
                                return creator
                return None
            
            creator = get_creator(filepaths, extension)
        
            # Add all the elements
            def add_element(directories, extension, parent_group = parent_path):
                for path in directories:
                    list_elements = []
                    group_created = False
                    for element in Path(path).rglob('*'):
                        if element.suffix == extension:
                            if not group_created:
                                try:
                                    self.handler.create_group(name = path.split('/')[-2], parent_group=parent_path)
                                    group_created = True
                                except:
                                    pass
                                parent = parent_group + "/" + path.split('/')[-2]
                            self.handler.import_raw_data(str(element), parent, creator=creator)
                        elif element.is_dir():
                            add_element([element], extension, parent_group)
            add_element(filepaths, extension)
        
        else:
            # Check all filepaths have same extension
            extensions = [Path(filepath).suffix for filepath in filepaths]
            if len(set(extensions)) > 1:
                QMessageBox.warning(self, "Error", "All filepaths must have the same extension.")
                return
        
            extension = extensions[0]
            if extension == ".h5":
                if not len(self.handler.wrp.get_children_elements()):
                    self.open_hdf5(filepaths[-1])
                else:
                    response = QMessageBox.question(self, "Addition or opening", "Do you want to add the HDF5 file to the current database or open the last one as a new database?", QMessageBox.Yes | QMessageBox.No |QMessageBox.Cancel)
                    if response == QMessageBox.Yes:
                        for filepath in filepaths:
                            self.handler.add_hdf5(filepath, parent_path)
                    elif response == QMessageBox.No:
                        self.open_hdf5(filepaths[-1])
            else:
                for filepath in filepaths:
                    try:
                        self.handler.import_raw_data(filepath, parent_path, creator=creator)
                        self.log.append(f"<i>{filepath}</i> imported to {parent_path} using {creator}")
                    except load_errors.LoadError_creator as e:
                        creator, ok = QInputDialog.getItem(self, "Select Creator", f"Multiple creators found. Please select one:", e.creators, 0, False)
                        if ok and creator:
                            self.handle_file_addition(filepaths, parent_path, creator)
                            break
                        else:
                            return
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Could not import {filepath}: {e}")
                        return

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

    def remove_element(self, path=None, next_path=None):
        """Remove the selected element from the HDF5 file.
        """
        if path is None:
            path = self.architecture_widget.get_current_path()

        if path == "Brillouin":
            QMessageBox.warning(self, "Warning", "You can't remove the root element")
            return
        
        # Determine fallback next path if not provided
        if next_path is None:
            next_path = "/".join(path.split('/')[:-1])

        dialog = QMessageBox.question(self, "Warning", f"Are you sure you want to remove <b>{path}</b>?")
        if dialog == QMessageBox.Yes:
            try:
                self.handler.delete_element(path)
                self.architecture_widget.update_treeview()
                self.architecture_widget.expand_path(next_path)
                self.properties_widget.update_properties(next_path)
                self.log.append(f"Element <i>{path}</i> removed")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not remove element: {e}")

    def remove_attribute(self):
        """Remove an attribute from the selected element.
        """
        QMessageBox.information(self, "Not implemented", "Remove attribute functionality is not yet implemented.")

    def rename_element(self, path):
        """Rename the selected element.
        """
        if path == "Brillouin":
            QMessageBox.warning(self, "Warning", "You can't rename the root element")
            return

        new_name, ok = QInputDialog.getText(self, "Rename Element", f"Enter new name for <b>{path}</b>:")
        if ok and new_name:
            try:
                self.handler.change_name(path, new_name)
                self.architecture_widget.update_treeview()
                self.architecture_widget.expand_path(path)
                self.properties_widget.update_properties(path)
                self.log.append(f"Element at <i>{path}</i> renamed to <i>{new_name}</i>")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not rename element: {e}")

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

    def treat_PSD(self, path = None):
        """Treat the PSD data.
        """
        if path is None:
            path = self.architecture_widget.get_current_path()
        
        if not path:
            QMessageBox.warning(self, "Warning", "Please select a group to treat.")
            return

        dialog = TreatWizard(self.handler, path, self)
        dialog.exec()

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())