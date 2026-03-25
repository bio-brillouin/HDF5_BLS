from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                               QTableWidget, QTableWidgetItem, QPushButton, 
                               QLabel, QInputDialog, QHeaderView, QComboBox, 
                               QStyledItemDelegate)
from PySide6.QtCore import Qt, Signal
from HDF5_BLS.normalized_attributes import NormalizedAttributes, Attribute

class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, owner, items):
        super().__init__(owner)
        self.items = items

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.setEditable(True)
        editor.addItems([str(i) for i in self.items])
        return editor

    def setEditorData(self, editor, index):
        value = index.data(Qt.EditRole)
        editor.setCurrentText(str(value) if value is not None else "")

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)

class AttributeEditDialog(QDialog):
    def __init__(self, handler, path, parent=None):
        super().__init__(parent)
        self.handler = handler
        self.path = path
        self.setWindowTitle(f"Edit Attributes - {path}")
        self.resize(600, 500)
        
        self.attributes_by_tab = {
            "Measure": [],
            "Spectrometer": [],
            "Other": []
        }
        
        self._initialize_ui()
        self._load_attributes()

    def _initialize_ui(self):
        self.layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.tables = {}
        
        for tab_name in self.attributes_by_tab.keys():
            table = QTableWidget(0, 3)
            table.setHorizontalHeaderLabels(["Attribute Name", "Value", "Units"])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            self.tabs.addTab(table, tab_name)
            self.tables[tab_name] = table
            
        self.layout.addWidget(self.tabs)
        
        # Add non-normalized attribute button
        self.btn_add_custom = QPushButton("Add non-normalized attribute")
        self.btn_add_custom.clicked.connect(self._add_custom_attribute)
        self.layout.addWidget(self.btn_add_custom)
        
        # OK / Cancel buttons
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        self.layout.addLayout(btn_layout)

    def _load_attributes(self):
        # 1. Get existing attributes from HDF5
        print(self.path)
        existing_attrs = self.handler.get_attributes(self.path)
        
        # 2. Get normalized attributes
        norm_attrs = NormalizedAttributes.get_all()
        
        # 3. Categorize them into tabs
        tab_data = {"Measure": [], "Spectrometer": [], "Other": []}
        
        # Keep track of which normalized attributes we've handled
        handled_norm = set()
        
        for attr in norm_attrs:
            full_name = attr.full_name
            val = existing_attrs.get(full_name, "")
            
            tab = "Other"
            if attr.group == "MEASURE": tab = "Measure"
            elif attr.group == "SPECTROMETER": tab = "Spectrometer"
            
            tab_data[tab].append((full_name, val, attr))
            handled_norm.add(full_name)
            
        # Then, add existing attributes that are NOT normalized to "Other"
        for key, val in existing_attrs.items():
            if key not in handled_norm:
                # Check if it was already in FILEPROP (which we map to Other anyway)
                attr_obj = None
                for attr in norm_attrs:
                    if attr.full_name == key:
                        attr_obj = attr
                        break
                tab_data["Other"].append((key, val, attr_obj))

        # Fill tables
        for tab, data in tab_data.items():
            table = self.tables[tab]
            table.setRowCount(len(data))
            for i, (name, val, attr_obj) in enumerate(data):
                # Name item (non-editable)
                name_item = QTableWidgetItem(name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                if attr_obj and attr_obj.description:
                    name_item.setToolTip(attr_obj.description)
                table.setItem(i, 0, name_item)
                
                # Value item
                val_item = QTableWidgetItem(str(val))
                table.setItem(i, 1, val_item)
                
                # If recommended values exist, use a delegate/combobox
                if attr_obj and attr_obj.recommended_values:
                    delegate = ComboBoxDelegate(table, attr_obj.recommended_values)
                    table.setItemDelegateForRow(i, delegate)

        # Fill tables
        for tab, data in tab_data.items():
            table = self.tables[tab]
            table.setRowCount(len(data))
            for i, (name, val, attr_obj) in enumerate(data):
                # Name item (non-editable)
                name_item = QTableWidgetItem(name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                if attr_obj and attr_obj.description:
                    name_item.setToolTip(attr_obj.description)
                table.setItem(i, 0, name_item)
                
                # Value item
                val_item = QTableWidgetItem(str(val))
                table.setItem(i, 1, val_item)
                
                # If recommended values exist, use a delegate/combobox
                if attr_obj and attr_obj.recommended_values:
                    delegate = ComboBoxDelegate(table, attr_obj.recommended_values)
                    table.setItemDelegateForRow(i, delegate)

    def _add_custom_attribute(self):
        name, ok = QInputDialog.getText(self, "New Attribute", "Define the name of the new non-normalized attribute:")
        if ok and name:
            table = self.tables["Other"]
            row = table.rowCount()
            table.insertRow(row)
            
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 0, name_item)
            
            val_item = QTableWidgetItem("")
            table.setItem(row, 1, val_item)
            
            units_item = QTableWidgetItem("") # For now custom units are empty or part of name
            table.setItem(row, 2, units_item)
            
            self.tabs.setCurrentWidget(table)

    def get_attributes(self):
        """Returns a dictionary of all attributes from the tables."""
        attrs = {}
        for table in self.tables.values():
            for row in range(table.rowCount()):
                name = table.item(row, 0).text()
                val = table.item(row, 1).text()
                if val: # Only save non-empty values? Or allow empty?
                    attrs[name] = val
        return attrs
