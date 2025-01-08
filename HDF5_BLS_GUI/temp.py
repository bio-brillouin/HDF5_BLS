import sys
import h5py
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg
from PySide6 import QtCore as qtc

class HDF5TreeViewer(qtw.QMainWindow):
    def __init__(self, file_path):
        super().__init__()
        self.setWindowTitle("HDF5 File Viewer")
        self.resize(800, 600)

        # Tree view setup
        self.tree_view = qtw.QTreeView(self)
        self.setCentralWidget(self.tree_view)

        # Model setup
        self.model = qtg.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Name", "Type"])
        self.tree_view.setModel(self.model)

        # Load the HDF5 file structure
        self.file_path = file_path
        self.load_hdf5_structure(file_path)

        # Connect item selection signal
        self.tree_view.selectionModel().selectionChanged.connect(self.item_selected)

    def load_hdf5_structure(self, file_path):
        """
        Loads the HDF5 file structure into the tree view.
        """
        with h5py.File(file_path, "r") as hdf_file:
            root_item = self.model.invisibleRootItem()
            self.add_hdf5_group_to_tree(hdf_file, root_item, "/")

    def add_hdf5_group_to_tree(self, group, parent_item, path):
        """
        Recursively adds HDF5 groups and datasets to the tree view.
        """
        for key in group:
            item_path = f"{path}/{key}".replace("//", "/")
            if isinstance(group[key], h5py.Group):
                # Add group item
                group_item = qtg.QStandardItem(key)
                group_item.setData(item_path, qtc.Qt.UserRole)  # Store the path
                type_item = qtg.QStandardItem("Group")
                parent_item.appendRow([group_item, type_item])

                # Recurse into the group
                self.add_hdf5_group_to_tree(group[key], group_item, item_path)
            elif isinstance(group[key], h5py.Dataset):
                # Add dataset item
                dataset_item = qtg.QStandardItem(key)
                dataset_item.setData(item_path, qtc.Qt.UserRole)  # Store the path
                type_item = qtg.QStandardItem("Dataset")
                parent_item.appendRow([dataset_item, type_item])

    @qtc.Slot(qtc.QItemSelection, qtc.QItemSelection)
    def item_selected(self, selected, deselected):
        """
        Prints the path of the selected item in the tree view.
        """
        indexes = self.tree_view.selectionModel().selectedIndexes()
        if indexes:
            selected_item = self.model.itemFromIndex(indexes[0])  # Get the first selected item
            item_path = selected_item.data(qtc.Qt.UserRole)  # Retrieve the stored path
            print(f"Selected item path: {item_path}")


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)

    # Replace 'example.h5' with your HDF5 file path
    file_path = '/Users/pierrebouvet/Documents/Databases/241105 - Water SNR TFP2 Felix/test.h5'
    viewer = HDF5TreeViewer(file_path)
    viewer.show()

    sys.exit(app.exec())
