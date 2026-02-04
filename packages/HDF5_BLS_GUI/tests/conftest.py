import pytest
import os
from PySide6.QtWidgets import QApplication
from HDF5_BLS_GUI.Main.main import MainWindow

@pytest.fixture
def main_window(qtbot):
    """Fixture to provide a MainWindow instance."""
    window = MainWindow()
    qtbot.add_widget(window)
    return window
