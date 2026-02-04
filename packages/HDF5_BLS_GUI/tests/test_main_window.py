import pytest
from HDF5_BLS_GUI.Main.main import MainWindow

def test_main_window_launch(qtbot):
    """Test that the main window launches and has the correct title."""
    window = MainWindow()
    qtbot.add_widget(window)
    window.show()
    
    assert window.windowTitle() != ""
    assert window.architecture_widget is not None
    assert window.button_panel is not None
    assert window.properties_widget is not None
    assert window.log_widget is not None

def test_main_window_elements_visible(qtbot):
    """Test that key UI elements are visible."""
    window = MainWindow()
    qtbot.add_widget(window)
    window.show()
    
    assert window.architecture_widget.isVisible()
    assert window.button_panel.isVisible()
    assert window.properties_widget.isVisible()
    assert window.log_widget.isVisible()
