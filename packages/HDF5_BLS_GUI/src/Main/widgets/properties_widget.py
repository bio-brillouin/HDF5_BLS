from PySide6.QtWidgets import QWidget, QTabWidget, QGridLayout, QTableView, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, Signal

class PropertiesWidget(QWidget):
    add_attribute_requested = Signal()
    remove_attribute_requested = Signal()

    def __init__(self, handler, config, parent=None):
        """Initializes the frame with the property tabs and the visualization tab.
        """
        super().__init__(parent)
        self.handler = handler
        self.config = config
        self._initialize_ui()

    def _initialize_ui(self):
        # Create the properties widget
        self.properties_tab_wdg = QTabWidget()

        # Create the four tabs
        self.properties_measure_wdg = QWidget()
        self.properties_tab_wdg.addTab(self.properties_measure_wdg, "Measure")
        msr_lyt = QGridLayout(self.properties_measure_wdg)

        self.properties_spectrometer_wdg = QWidget()
        self.properties_tab_wdg.addTab(self.properties_spectrometer_wdg, "Spectrometer")
        spc_lyt = QGridLayout(self.properties_spectrometer_wdg)

        self.properties_other_wdg = QWidget()
        self.properties_tab_wdg.addTab(self.properties_other_wdg, "Other")
        oth_lyt = QGridLayout(self.properties_other_wdg)

        self.visualization_wdg = QWidget()
        self.properties_tab_wdg.addTab(self.visualization_wdg, "Visualization")
        vis_lyt = QGridLayout(self.visualization_wdg)

        # Create the tableviews for the tabs
        self.properties_measure_tableview = QTableView()
        msr_lyt.addWidget(self.properties_measure_tableview, 0, 0, 1, 1)
        msr_lyt.setContentsMargins(0, 0, 0, 0)
        
        self.properties_spectrometer_tableview = QTableView()
        spc_lyt.addWidget(self.properties_spectrometer_tableview, 0, 0, 1, 1)
        spc_lyt.setContentsMargins(0, 0, 0, 0)
        
        self.properties_other_tableview = QTableView()
        oth_lyt.addWidget(self.properties_other_tableview, 0, 0, 1, 1)
        oth_lyt.setContentsMargins(0, 0, 0, 0)

        # Create the models for the tableviews
        self.properties_measure_model = QStandardItemModel()
        self.properties_measure_model.setHorizontalHeaderLabels(["Name", "Value", "Units"])
        self.properties_measure_tableview.setModel(self.properties_measure_model)
        
        self.properties_spectrometer_model = QStandardItemModel()
        self.properties_spectrometer_model.setHorizontalHeaderLabels(["Name", "Value", "Units"])
        self.properties_spectrometer_tableview.setModel(self.properties_spectrometer_model)
        
        self.properties_other_model = QStandardItemModel()
        self.properties_other_model.setHorizontalHeaderLabels(["Name", "Value", "Units"])
        self.properties_other_tableview.setModel(self.properties_other_model)

        # Add buttons for adding and removing attributes
        self.properties_buttons_layout = QHBoxLayout()
        self.btn_add_attribute = QPushButton("Add Attribute")
        self.btn_remove_attribute = QPushButton("Remove Attribute")
        self.properties_buttons_layout.addWidget(self.btn_add_attribute)
        self.properties_buttons_layout.addWidget(self.btn_remove_attribute)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.properties_tab_wdg)
        self.main_layout.addLayout(self.properties_buttons_layout)
        
        # Connect buttons
        self.btn_add_attribute.clicked.connect(self.add_attribute_requested)
        self.btn_remove_attribute.clicked.connect(self.remove_attribute_requested)

    def update_properties(self, path):
        """Update the properties frame based on the selected path.
        """
        if not path:
            return
            
        attr = self.handler.get_attributes(path)

        # Update the tables
        self.properties_measure_model.clear()
        self.properties_measure_model.setHorizontalHeaderLabels(["Name", "Value", "Units"])
        self.properties_spectrometer_model.clear()
        self.properties_spectrometer_model.setHorizontalHeaderLabels(["Name", "Value", "Units"])
        self.properties_other_model.clear()
        self.properties_other_model.setHorizontalHeaderLabels(["Name", "Value", "Units"])

        for k, v in attr.items():
            try:
                if "." in k:
                    cat, name_raw = k.split(".")
                    name_parts = name_raw.split("_")
                    if name_parts[-1].startswith("(") and name_parts[-1].endswith(")"):
                        unit = name_parts.pop(-1)[1:-1]
                    else:
                        unit = ""
                    name = " ".join(name_parts)
                    
                    value = str(v)
                    if len(value) > 100: value = value[:100] + "..."
                    
                    row = [QStandardItem(name), QStandardItem(value), QStandardItem(unit)]
                    
                    if cat == "MEASURE":
                        self.properties_measure_model.appendRow(row)
                    elif cat == "SPECTROMETER":
                        self.properties_spectrometer_model.appendRow(row)
                    else:
                        self.properties_other_model.appendRow([QStandardItem(k.replace("_", " ")), QStandardItem(value), QStandardItem(unit)])
                else:
                    value = str(v)
                    if len(value) > 100: value = value[:100] + "..."
                    self.properties_other_model.appendRow([QStandardItem(k.replace("_", " ")), QStandardItem(value), QStandardItem("")])
            except:
                pass
