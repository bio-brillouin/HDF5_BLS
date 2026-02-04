from PySide6.QtWidgets import QTreeView, QAbstractItemView, QMenu, QMessageBox
from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtGui import QIcon, QStandardItem, QAction
from ..models import TreeviewItemModel
from HDF5_BLS.wrapper import HDF5_group, HDF5_dataset

class ArchitectureWidget(QTreeView):
    selection_changed = Signal(str)  # Emits the path of the selected element
    rename_requested = Signal(str, str)  # Emits (old_path, new_name)
    delete_requested = Signal(str)
    add_group_requested = Signal(str)
    import_data_requested = Signal(str)
    files_dropped = Signal(list, str) # paths, target_path
    process_psd_requested = Signal(list) # paths
    treat_requested = Signal(list) # paths

    def __init__(self, handler, config, gui_root, parent=None):
        """Initializes the architecture frame with the treeview.
        """
        super().__init__(parent)
        self.handler = handler
        self.config = config
        self.gui_root = gui_root

        # Create the model displayed in the treeview
        self.architecture_file_model = TreeviewItemModel()
        self.setModel(self.architecture_file_model)

        # Connects selection change
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)

        # Connects data change for renames
        self.architecture_file_model.dataChanged.connect(self._on_data_changed)

        # UI Setup
        self.setAcceptDrops(True)
        self.setDragEnabled(False)
        self.setDragDropMode(QAbstractItemView.DropOnly)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setStyleSheet("QTreeView::item:selected { background-color: lightblue; color: black; }")
        
        self.expanded.connect(self._adjust_columns)

        # Hover timer for auto-expand
        self.current_hover_index = None
        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self._expand_on_hover)

    def update_treeview(self):
        """Recreates the model of the treeview with the content of the HDF5 file.
        """
        def fill(item: QStandardItem = QStandardItem("Brillouin"), parent: str = "Brillouin"):
            if parent == "Brillouin":
                item.setData("Brillouin", Qt.UserRole)
            
            for elt in self.handler.get_children_elements(path=parent):
                loc_item = QStandardItem(elt)
                path = f"{parent}/{elt}"
                loc_item.setData(path, Qt.UserRole)
                self._set_icon(loc_item, self.handler.get_type(path=path, return_Brillouin_type=True))
                
                temp = [loc_item]
                attributes = self.handler.get_attributes(path=path)
                
                for properties in self.config['Treeview']['columns'].split(',')[1:]:
                    if properties in attributes:
                        temp.append(QStandardItem(str(attributes[properties])))
                    else:
                        temp.append(QStandardItem(""))
                
                item.appendRow(temp)
                fill(loc_item, path)
            return item

        self.architecture_file_model.clear()
        
        # Setup Headers
        temp = self.config['Treeview']['columns'].split(',')
        columns = []
        for e in temp:
            if "MEASURE." in e: columns.append(e[8:].replace("_", " "))
            elif "SPECTROMETER." in e: columns.append(e[13:].replace("_", " "))
            elif "FILEPROP." in e: columns.append(e[10:].replace("_", " "))
            else: columns.append(e.replace("_", " "))
        
        self.architecture_file_model.setHorizontalHeaderLabels(columns)
        root_item = fill()
        self.architecture_file_model.appendRow([root_item])
        
        # Select first element
        self.setCurrentIndex(self.architecture_file_model.index(0, 0))

    def _set_icon(self, item, brillouin_type):
        if "Abscissa" in brillouin_type:
            brillouin_type = "Abscissa"
        item.setIcon(QIcon(f"{self.gui_root}/assets/img/{brillouin_type}.svg"))

    def _on_selection_changed(self, selected, deselected):
        index = self.currentIndex()
        if index.isValid():
            path = index.data(Qt.UserRole) or "Brillouin"
            self.selection_changed.emit(path)

    def get_current_path(self):
        index = self.currentIndex()
        if index.isValid():
            return index.data(Qt.UserRole) or "Brillouin"
        return "Brillouin"

    def _on_data_changed(self, topLeft, bottomRight, roles):
        # Handle renames
        item = self.architecture_file_model.itemFromIndex(topLeft)
        # This part requires matching the path rename in the HDF5 file
        # For simplicity in this first refactor pass, we might emit a signal
        # or handle it if we have the old path.
        pass

    def _adjust_columns(self, index):
        self.resizeColumnToContents(0)

    def _expand_on_hover(self):
        if self.current_hover_index and self.current_hover_index.isValid():
            self.expand(self.current_hover_index)

    def show_context_menu(self, position: QPoint):
        index = self.indexAt(position)
        if not index.isValid():
            return

        path = index.data(Qt.UserRole) or "Brillouin"
        menu = QMenu()
        
        # Add actions based on path/type
        # (This will be a simplified version, can be expanded)
        add_group_action = menu.addAction("Add Group")
        add_group_action.triggered.connect(lambda: self.add_group_requested.emit(path))
        
        remove_action = menu.addAction("Remove Element")
        if path == "Brillouin":
            remove_action.setEnabled(False)
        remove_action.triggered.connect(lambda: self.delete_requested.emit(path))
        
        menu.exec_(self.viewport().mapToGlobal(position))

    # Drag and Drop simplified
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = [url.toLocalFile() for url in event.mimeData().urls()]
            # Emit signal for import
            index = self.indexAt(event.position().toPoint())
            path = index.data(Qt.UserRole) if index.isValid() else "Brillouin"
            self.files_dropped.emit(urls, path)
            event.accept()
        else:
            super().dropEvent(event)
