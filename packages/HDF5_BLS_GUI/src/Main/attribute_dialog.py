from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QStackedWidget, QWidget
from PySide6.QtCore import Qt
from HDF5_BLS import NormalizedAttributes

class PlaceholderLineEdit(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.placeholder_text = placeholder
        self.is_placeholder_active = False
        
    def set_placeholder_text(self, text):
        self.placeholder_text = text
        if not self.text() or self.is_placeholder_active:
            self.show_placeholder()

    def show_placeholder(self):
        self.setText(self.placeholder_text)
        self.setStyleSheet("color: grey; font-style: italic;")
        self.is_placeholder_active = True
        
    def focusInEvent(self, event):
        if self.is_placeholder_active:
            self.clear()
            self.setStyleSheet("")
            self.is_placeholder_active = False
        super().focusInEvent(event)
        
    def focusOutEvent(self, event):
        if not self.text():
            self.show_placeholder()
        super().focusOutEvent(event)

class AddAttributeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Attribute")
        self.setMinimumWidth(450)
        
        self.main_layout = QVBoxLayout(self)
        
        # Line 1: Group
        group_layout = QHBoxLayout()
        group_label = QLabel("Add attribute from group:")
        group_layout.addWidget(group_label)
        self.group_combo = QComboBox()
        self.group_combo.addItems(NormalizedAttributes.get_groups())
        self.group_combo.currentTextChanged.connect(self.on_group_changed)
        group_layout.addWidget(self.group_combo)
        self.main_layout.addLayout(group_layout)
        
        # Line 2: Attribute Name
        name_layout = QHBoxLayout()
        name_label = QLabel("attribute name:")
        name_layout.addWidget(name_label)
        self.name_stack = QStackedWidget()
        
        # Combo for existing names
        self.name_combo = QComboBox()
        self.name_combo.currentTextChanged.connect(self.on_name_changed)
        self.name_stack.addWidget(self.name_combo)
        
        # Line edit for new names
        self.name_edit = PlaceholderLineEdit()
        self.name_stack.addWidget(self.name_edit)
        
        name_layout.addWidget(self.name_stack)
        
        self.btn_new_name = QPushButton("new name")
        self.btn_new_name.setFixedWidth(100)
        self.btn_new_name.clicked.connect(self.toggle_new_name)
        name_layout.addWidget(self.btn_new_name)
        self.main_layout.addLayout(name_layout)
        
        # Line 3: Value
        value_layout = QHBoxLayout()
        value_label = QLabel("Value:")
        value_layout.addWidget(value_label)
        self.value_stack = QStackedWidget()
        
        # Combo for recommended values
        self.value_combo = QComboBox()
        self.value_stack.addWidget(self.value_combo)
        
        # Line edit for custom values
        self.value_edit = QLineEdit()
        self.value_stack.addWidget(self.value_edit)
        
        value_layout.addWidget(self.value_stack)
        
        self.btn_custom_value = QPushButton("custom")
        self.btn_custom_value.setFixedWidth(100)
        self.btn_custom_value.clicked.connect(self.toggle_custom_value)
        value_layout.addWidget(self.btn_custom_value)
        self.main_layout.addLayout(value_layout)
        
        # OK / Cancel
        buttons_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btn_ok)
        buttons_layout.addWidget(self.btn_cancel)
        self.main_layout.addLayout(buttons_layout)
        
        # Initialize
        if self.group_combo.count() > 0:
            self.on_group_changed(self.group_combo.currentText())

    def on_group_changed(self, group):
        self.name_combo.clear()
        attrs = NormalizedAttributes.get_attributes_by_group(group)
        self.name_combo.addItems([a.name for a in attrs])
        if self.name_combo.count() > 0:
            self.on_name_changed(self.name_combo.currentText())

    def on_name_changed(self, name):
        if self.name_stack.currentIndex() == 1: # If in "new name" mode, don't update value view based on name combo
            return
            
        group = self.group_combo.currentText()
        attrs = NormalizedAttributes.get_attributes_by_group(group)
        attr = next((a for a in attrs if a.name == name), None)
        
        if attr and attr.recommended_values:
            self.value_combo.clear()
            self.value_combo.addItems(map(str, attr.recommended_values))
            self.value_stack.setCurrentIndex(0) # Show combo
            self.btn_custom_value.setVisible(True)
            self.btn_custom_value.setText("custom")
        else:
            self.value_stack.setCurrentIndex(1) # Show edit
            self.btn_custom_value.setVisible(False)

    def toggle_new_name(self):
        if self.name_stack.currentIndex() == 0:
            self.name_stack.setCurrentIndex(1)
            self.name_edit.set_placeholder_text("Attribue_name_(unit)")
            self.btn_new_name.setText("existing")
            self.value_stack.setCurrentIndex(1) # Custom name implies custom value entry usually
            self.btn_custom_value.setVisible(False)
        else:
            self.name_stack.setCurrentIndex(0)
            self.btn_new_name.setText("new name")
            self.on_name_changed(self.name_combo.currentText())

    def toggle_custom_value(self):
        if self.value_stack.currentIndex() == 0:
            self.value_stack.setCurrentIndex(1)
            self.btn_custom_value.setText("recommended")
        else:
            self.value_stack.setCurrentIndex(0)
            self.btn_custom_value.setText("custom")

    def get_data(self):
        group = self.group_combo.currentText()
        if self.name_stack.currentIndex() == 0:
            name = self.name_combo.currentText()
        else:
            if self.name_edit.is_placeholder_active:
                name = ""
            else:
                name = self.name_edit.text()
            
        full_name = f"{group}.{name}"
        
        if self.value_stack.currentIndex() == 0:
            value = self.value_combo.currentText()
        else:
            value = self.value_edit.text()
            
        return full_name, value
