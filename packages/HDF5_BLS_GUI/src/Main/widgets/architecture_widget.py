from PySide6.QtWidgets import QTreeView, QAbstractItemView, QMenu, QMessageBox
from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtGui import QIcon, QStandardItem, QAction
from ..models import TreeviewItemModel
from HDF5_BLS.wrapper import HDF5_group, HDF5_dataset

class ArchitectureWidget(QTreeView):
    selection_changed = Signal(str)  # Emits the path of the selected element
    rename_requested = Signal(str)  # Emits (path)
    delete_requested = Signal(str, str) # Emits (path_to_delete, path_to_select_after)
    add_group_requested = Signal(str) # path
    change_type_requested = Signal(str, str) # path, brillouin_type
    export_path_clipboard = Signal(str) # path
    export_group_requested = Signal(str) # path
    files_dropped = Signal(list, str) # paths, target_path
    import_data_requested = Signal(str) # path
    process_psd_requested = Signal(list) # paths
    update_property_requested = Signal(str) # path
    treat_requested = Signal(list) # paths
    treat_PSD_requested = Signal(str) # paths
    analyze_raw_data_requested = Signal(str) # paths

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
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
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

    def update_icon(self, path: str):
        """Updates the icon of an element in the treeview.
        """
        loc_item = self.find_item_by_path(path)
        if loc_item:
            self._set_icon(loc_item, self.handler.get_type(path=path, return_Brillouin_type=True))

    def find_item_by_path(self, path: str):
        """Finds a QStandardItem in the model by its full HDF5 path.
        """
        # The root is always "Brillouin"
        root_item = self.architecture_file_model.item(0)
        if not root_item:
            return None
        
        if path == "Brillouin":
            return root_item
        
        parts = path.split("/")
        if parts[0] != "Brillouin":
            return None
            
        current_item = root_item
        for part in parts[1:]:
            found = False
            for i in range(current_item.rowCount()):
                child = current_item.child(i)
                if child and child.text() == part:
                    current_item = child
                    found = True
                    break
            if not found:
                return None
        return current_item

    def update_treeview(self):
        """Recreates the model of the treeview with the content of the HDF5 file.
        """
        def fill(item: QStandardItem = QStandardItem("Brillouin"), parent: str = "Brillouin"):
            if parent == "Brillouin":
                item.setData("Brillouin", Qt.UserRole)
            
            for elt in self.handler.get_children_elements(path=parent):
                loc_item = QStandardItem(elt)
                if not elt == "Brillouin":
                    loc_item.setEditable(True)
                else:
                    loc_item.setEditable(False)
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
        root_item.setEditable(False) # Ensure root "Brillouin" is not editable
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
        if Qt.EditRole in roles or not roles:
            item = self.architecture_file_model.itemFromIndex(topLeft)
            if not item:
                return

            old_path = item.data(Qt.UserRole)
            if not old_path:
                return
            
            new_name = item.text()
            old_name = old_path.split("/")[-1]

            if new_name != old_name:
                try:
                    # Rename in HDF5
                    self.handler.change_name(old_path, new_name)
                    
                    # Update paths recursively
                    new_path = "/".join(old_path.split("/")[:-1]) + "/" + new_name
                    self._update_item_paths(item, new_path)
                    
                    # Notify UI if needed (already handled by model for text)
                except Exception as e:
                    # Revert name on error
                    item.setText(old_name)
                    QMessageBox.warning(self, "Rename Error", f"Could not rename element: {e}")

    def _update_item_paths(self, item, new_path):
        """Recursively update the UserRole path for an item and all its children.
        """
        item.setData(new_path, Qt.UserRole)
        for i in range(item.rowCount()):
            child = item.child(i)
            if child:
                child_name = child.data(Qt.UserRole).split("/")[-1]
                self._update_item_paths(child, f"{new_path}/{child_name}")

    def _adjust_columns(self, index):
        self.resizeColumnToContents(0)

    def _expand_on_hover(self):
        if self.current_hover_index and self.current_hover_index.isValid():
            self.expand(self.current_hover_index)

    def expand_path(self, path: str):
        """Expand the treeview to the given path.
        """
        item = self.find_item_by_path(path)
        if item:
            index = self.architecture_file_model.indexFromItem(item)
            self.expand(index)
            self.setCurrentIndex(index)
            self.update_property_requested.emit(path)

    def edit_path(self, path: str):
        """Trigger editing of the item at the given path.
        """
        item = self.find_item_by_path(path)
        if item:
            index = item.index()
            self.setCurrentIndex(index)
            self.edit(index)

    def show_context_menu(self, position: QPoint):
        def general_actions():
            if not path == "Brillouin":
                rename_action = menu.addAction("Rename")
                rename_action.triggered.connect(lambda: self.rename_requested.emit(path))

            export_path_action = menu.addAction("Export path to clipboard")
            export_path_action.triggered.connect(lambda: self.export_path_clipboard.emit(path))

            if not path == "Brillouin":
                remove_action = menu.addAction("Delete")
                # Find index above for selection after delete
                above_index = self.indexAbove(index)
                above_path = above_index.data(Qt.UserRole) if above_index.isValid() else "Brillouin"
                remove_action.triggered.connect(lambda: self.delete_requested.emit(path, above_path))

            menu.addSeparator()

            import_data_action = menu.addAction("Import Data")
            import_data_action.triggered.connect(lambda: self.import_data_requested.emit(path))

        def group_actions(path):
            def sub_menu_Brillouin_type_group():
                try: change_type_dataset_action.clear()
                except: pass

                try: change_type_group_action.clear()
                except: pass

                dic_brillouin_type_groups = {}
                for tpe in self.handler.wrp.BRILLOUIN_TYPES_GROUPS:
                    dic_brillouin_type_groups[tpe] = QAction(tpe.replace("_", " "), self)
                    # Capture tpe as a default argument to avoid late binding issues
                    dic_brillouin_type_groups[tpe].triggered.connect(lambda _, t=tpe: self.change_type_requested.emit(path, str(t)))
                    change_type_group_action.addAction(dic_brillouin_type_groups[tpe])

            def special_actions_PSD(path):
                ret = False
                has_raw, has_PSD, has_frequency = False, False, False
                for e in self.handler.wrp.get_children_elements(path = path):
                    if self.handler.wrp.get_type(path=f'{path}/{e}', return_Brillouin_type=True) == "PSD":
                        has_PSD = True
                    elif self.handler.wrp.get_type(path=f'{path}/{e}', return_Brillouin_type=True) == "Frequency":
                        has_frequency = True
                    elif self.handler.wrp.get_type(path=f'{path}/{e}', return_Brillouin_type=True) == "Raw_data":
                        has_raw = True
                
                if has_raw:
                    get_PSD_action = menu.addAction("Analyze Raw data")
                    get_PSD_action.triggered.connect(lambda: self.analyze_raw_data_requested.emit(path))
                    ret = True
                
                if has_PSD and has_frequency:
                    get_PSD_action = menu.addAction("Treat PSD")
                    get_PSD_action.triggered.connect(lambda: self.treat_PSD_requested.emit(path))
                    ret = True

                return ret
            
            add_group_action = menu.addAction("New sub-group")
            add_group_action.triggered.connect(lambda: self.add_group_requested.emit(path))

            export_group_action = menu.addAction("Export Group as HDF5 file")
            export_group_action.triggered.connect(lambda: self.export_group_requested.emit(path))

            menu.addSeparator()

            change_type_group_action = menu.addMenu("Edit Type")
            change_type_group_action.aboutToShow.connect(sub_menu_Brillouin_type_group)

            menu.addSeparator()

            if special_actions_PSD(path):
                menu.addSeparator()

        def dataset_actions():
            pass
            # change_type_action = menu.addAction("Change Type")
            # change_type_action.triggered.connect(lambda: self.change_type_requested.emit(path))

        index = self.indexAt(position)
        if not index.isValid():
            return

        # Get the path of the element, whether it is a group or a dataset, and its Brillouin type
        path = index.data(Qt.UserRole) or "Brillouin"
        brillouin_type = index.data(Qt.UserRole + 1) or "Brillouin"
        is_group = self.handler.get_type(path=path, return_Brillouin_type=False) == HDF5_group
        
        # Create context menu
        menu = QMenu()
        menu_actions = {}
        associated_action = {}
        
        # Add actions based on path/type
        general_actions()
        if is_group:
            group_actions(path)
        else:
            menu.addSeparator()
            dataset_actions()
        
        menu.exec_(self.viewport().mapToGlobal(position))

    # Drag and Drop simplified
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        elif event.mimeData().hasText(): # Internal drag
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        elif event.mimeData().hasText(): # Internal drag
            # Expand group on hover
            index = self.indexAt(event.position().toPoint())
            if index.isValid():
                self.expand(index)
            
            # Show the green "+" by using CopyAction (per user request)
            event.setDropAction(Qt.CopyAction)
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
            self.update_treeview()
            self.expand_path(path)
        elif event.mimeData().hasText(): # Internal drop
            old_paths = event.mimeData().text().split(",")
            index = self.indexAt(event.position().toPoint())
            new_parent = index.data(Qt.UserRole) if index.isValid() else "Brillouin"
            
            # If dropped on a dataset, move to its parent instead? 
            # Or just follow the folder metaphor.
            if self.handler.get_type(new_parent) == HDF5_dataset:
                new_parent = "/".join(new_parent.split("/")[:-1])

            try:
                for old_path in old_paths:
                    if old_path != new_parent and not new_parent.startswith(old_path + "/"):
                        self.handler.move_element(old_path, new_parent)
                
                event.accept()
                self.update_treeview()
                self.expand_path(new_parent)
                self.selection_changed.emit(new_parent) # Update properties as requested
            except Exception as e:
                QMessageBox.warning(self, "Move Error", f"Could not move element: {e}")
        else:
            super().dropEvent(event)

    def keyPressEvent(self, event):
        """Handle key presses for delete shortcut.
        """
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            index = self.currentIndex()
            if index.isValid():
                path = index.data(Qt.UserRole)
                if path and path != "Brillouin":
                    # Get item above before deleting
                    above_index = self.indexAbove(index)
                    above_path = above_index.data(Qt.UserRole) if above_index.isValid() else "Brillouin"
                    
                    self.delete_requested.emit(path, above_path)
        else:
            super().keyPressEvent(event)
