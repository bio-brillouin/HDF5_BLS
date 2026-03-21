import os
import numpy as np
import inspect
from pathlib import Path
from configparser import ConfigParser
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QTreeView, QWidget, QSpinBox, QCheckBox, 
    QFrame, QSplitter, QMessageBox, QMenu, QSizePolicy
)
from PySide6.QtGui import QStandardItemModel, QStandardItem

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from HDF5_BLS_treat import Treat
from MessageBox_multiple_choice.main import MessageBoxMultipleChoice
from algorithm_wizard.main import AlgorithmWizard

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

class TreatWizard(QDialog):
    def __init__(self, handler, path, parent=None):
        super().__init__(parent)
        self.handler = handler
        self.path = path
        
        self.gui_root = str(Path(__file__).resolve().parent.parent.parent)

        # Load config file
        self.config = ConfigParser()
        self.config.read(f"{Path(__file__).resolve().parent}/config_Treat.ini")

        self.setWindowTitle("HDF5_BLS_treat wizard")
        self.setGeometry(self.config["Geometry"].getint("x"),
                         self.config["Geometry"].getint("y"),
                         self.config["Geometry"].getint("width"),
                         self.config["Geometry"].getint("height"))

        # Initialize Treat object
        self._load_data()
        self.treat = Treat(self.frequency, self.psd)

        self._setup_ui()
        self._connect_signals()
        self._update_graph()

    def _load_data(self):
        """Loads PSD and Frequency data from the wrapper."""
        self.psd = None
        self.frequency = None
        
        # Search for PSD and Frequency datasets in the group
        for child in self.handler.wrp.get_children_elements(path=self.path):
            child_path = f"{self.path}/{child}"
            b_type = self.handler.wrp.get_type(path=child_path, return_Brillouin_type=True)
            if b_type == "PSD":
                self.psd = self.handler.wrp[child_path]
            elif b_type == "Frequency":
                self.frequency = self.handler.wrp[child_path]
        
        if self.psd is None or self.frequency is None:
            # Create dummy data if not found (for demonstration/safety)
            if self.psd is None: self.psd = np.zeros((10, 10, 512))
            if self.frequency is None: self.frequency = np.linspace(0, 10, 512)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Splitter for Left and Right frames
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)

        # --- Left Frame ---
        self.left_widget = QWidget()
        left_layout = QVBoxLayout(self.left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Dimension Navigation Subframe
        self.dim_nav_frame = QFrame()
        self.dim_nav_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.dim_nav_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        
        dim_layout = QGridLayout(self.dim_nav_frame)
        self.dim_controls = []
        for i in range(len(self.psd.shape) - 1):
            lbl = QLabel(f"Dimension {i}:")
            spin = QSpinBox()
            spin.setRange(0, self.psd.shape[i] - 1)
            spin.valueChanged.connect(self._update_graph)
            
            chk = QCheckBox("Average")
            chk.stateChanged.connect(self._update_graph)
            
            dim_layout.addWidget(lbl, i, 0)
            dim_layout.addWidget(spin, i, 1)
            dim_layout.addWidget(chk, i, 2)
            
            self.dim_controls.append({'spin': spin, 'chk': chk})
            
        left_layout.addWidget(self.dim_nav_frame)
        
        # Graph Frame
        self.canvas = MplCanvas(self)
        self.toolbar = NavigationToolbar(self.canvas, self)
        left_layout.addWidget(self.toolbar)
        left_layout.addWidget(self.canvas)
        
        # --- Right Frame ---
        self.right_widget = QWidget()
        right_layout = QVBoxLayout(self.right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.b_algorithm = QPushButton("Algorithm")
        self.b_algorithm.setStyleSheet("font-weight: bold; height: 30px;")
        right_layout.addWidget(self.b_algorithm)
        
        self.tree_steps = QTreeView()
        self.model_steps = QStandardItemModel()
        self.model_steps.setHorizontalHeaderLabels(["Step / Parameter", "Value"])
        self.tree_steps.setModel(self.model_steps)
        right_layout.addWidget(self.tree_steps)
        
        # Buttons subframe
        btn_subframe = QWidget()
        btn_sub_layout = QHBoxLayout(btn_subframe)
        btn_sub_layout.setContentsMargins(0, 0, 0, 0)
        self.b_add_step = QPushButton("Add step")
        self.b_del_step = QPushButton("Delete step")
        btn_sub_layout.addWidget(self.b_add_step)
        btn_sub_layout.addWidget(self.b_del_step)
        right_layout.addWidget(btn_subframe)
        
        self.b_apply_all = QPushButton("Apply on all")
        self.b_apply_all.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold;")
        right_layout.addWidget(self.b_apply_all)
        
        # Add to splitter
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)

        # --- Bottom Buttons ---
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.b_cancel = QPushButton("Cancel")
        self.b_cancel.setFixedWidth(100)
        bottom_layout.addWidget(self.b_cancel)
        main_layout.addLayout(bottom_layout)

    def _connect_signals(self):
        self.b_add_step.clicked.connect(self._add_step)
        self.b_del_step.clicked.connect(self._delete_step)
        self.b_apply_all.clicked.connect(self._apply_on_all)
        self.b_algorithm.clicked.connect(self._show_algorithm_menu)
        self.b_cancel.clicked.connect(self._cancel)

    def _update_graph(self):
        """Updates the graph based on dimension selection/averaging."""
        data = self.psd
        
        # Determine slices
        final_slices = []
        axes_to_average = []
        for i, ctrl in enumerate(self.dim_controls):
            if ctrl['chk'].isChecked():
                final_slices.append(slice(None))
                axes_to_average.append(i)
            else:
                final_slices.append(ctrl['spin'].value())
        
        # Navigate to the sub-array
        sub_data = data[tuple(final_slices)]
        
        # Average if needed
        if axes_to_average and len(sub_data.shape) > 1:
            # Simple mean over all non-frequency axes in the sub-selection
            current_psd = np.mean(sub_data, axis=tuple(range(len(sub_data.shape)-1)))
        else:
            current_psd = sub_data

        self.canvas.axes.clear()
        self.canvas.axes.plot(self.frequency, current_psd)
        self.canvas.axes.set_xlabel("Frequency")
        self.canvas.axes.set_ylabel("Intensity")
        self.canvas.axes.grid(True, which='both', linestyle='--', alpha=0.5)
        self.canvas.draw()

    def _add_step(self):
        """Allows user to pick a method from Treat object and add it as a step."""
        # Get public methods of Treat that are not 'silent_*' or inheritance-related
        methods = [m for m, _ in inspect.getmembers(self.treat, predicate=inspect.ismethod)
                   if not m.startswith('_') and not m.startswith('silent_')]
        
        choice, result = MessageBoxMultipleChoice.get_choice("Select a processing step to add:", methods, parent=self)
        if result == "ok":
            method = getattr(self.treat, choice)
            # Call method (this might trigger record_algorithm if decorated)
            method()
            self._update_treeview()

    def _delete_step(self):
        """Deletes the selected step from the algorithm."""
        index = self.tree_steps.currentIndex()
        if not index.isValid():
            QMessageBox.information(self, "Delete step", "Please select a step to delete.")
            return
        
        # If a child (parameter) is selected, get its parent (the function)
        if index.parent().isValid():
            index = index.parent()
            
        row = index.row()
        self.treat.silent_remove_step(step=row)
        self._update_treeview()

    def _apply_on_all(self):
        """Applies the current algorithm on all spectra."""
        self.treat.apply_algorithm_on_all()
        # You might want to show a progress bar or success message
        QMessageBox.information(self, "Success", "Algorithm applied on all spectra.")

    def _show_algorithm_menu(self):
        """Shows options for the algorithm (Save, Open, New)."""
        menu = QMenu(self)
        new_act = menu.addAction("New Algorithm")
        
        # Check if algorithm is already named or has steps to Decide if we show Edit
        has_algo = self.treat._algorithm.get("name") != "Algorithm" or len(self.treat._algorithm.get("functions", [])) > 0
        edit_act = None
        if has_algo:
            edit_act = menu.addAction("Edit Algorithm")
            
        open_act = menu.addAction("Open Algorithm")
        save_act = menu.addAction("Save Algorithm")
        
        action = menu.exec(self.b_algorithm.mapToGlobal(QPoint(0, self.b_algorithm.height())))
        
        if action == new_act:
            self._open_algorithm_wizard(edit=False)
        elif action == edit_act:
            self._open_algorithm_wizard(edit=True)
        elif action == open_act:
            # Should use QFileDialog here (handled later or existing logic)
            pass
        elif action == save_act:
            # Should use QFileDialog here (handled later or existing logic)
            pass

    def _open_algorithm_wizard(self, edit=False):
        """Opens the algorithm wizard dialog."""
        if edit:
            algo = self.treat._algorithm
            dialog = AlgorithmWizard(
                title=algo.get("name", ""),
                version=algo.get("version", "0.1"),
                author=algo.get("author", ""),
                institution=algo.get("institution", ""),
                description=algo.get("description", ""),
                parent=self
            )
        else:
            dialog = AlgorithmWizard(parent=self)

        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()

            self.treat.silent_create_algorithm(
                algorithm_name=data["name"],
                version=data["version"],
                author=data["author"],
                description=data["description"]
            )
            
            # Update button name
            self.b_algorithm.setText(data["name"])
            self._update_treeview()

    def _cancel(self):
        """Destroys the Treat object and closes the dialog."""
        if hasattr(self, 'treat'):
            del self.treat
        self.reject()

    def _update_treeview(self):
        """Refreshes the treeview based on Treat._algorithm."""
        self.model_steps.clear()
        self.model_steps.setHorizontalHeaderLabels(["Step / Parameter", "Value"])
        
        # Algorithm is stored in self.treat._algorithm
        if hasattr(self.treat, '_algorithm'):
            for i, step in enumerate(self.treat._algorithm.get('functions', [])):
                func_item = QStandardItem(step['function'])
                func_item.setData(i, Qt.UserRole)
                
                for param, value in step.get('parameters', {}).items():
                    param_item = QStandardItem(param)
                    val_item = QStandardItem(str(value))
                    func_item.appendRow([param_item, val_item])
                
                self.model_steps.appendRow(func_item)
        
        self.tree_steps.expandAll()
