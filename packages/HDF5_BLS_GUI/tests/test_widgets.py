import pytest
from PySide6.QtCore import Qt
from HDF5_BLS_GUI.Main.widgets.button_panel import ButtonPanel
from HDF5_BLS_GUI.Main.widgets.architecture_widget import ArchitectureWidget
from HDF5_BLS_GUI.Main.logic.hdf5_handler import HDF5Handler
from configparser import ConfigParser
import os

@pytest.fixture
def config():
    cfg = ConfigParser()
    cfg.add_section('Default_contents')
    cfg.set('Default_contents', 'title', 'Test Window')
    cfg.add_section('Geometry')
    cfg.set('Geometry', 'x', '100')
    cfg.set('Geometry', 'y', '100')
    cfg.set('Geometry', 'width', '800')
    cfg.set('Geometry', 'height', '600')
    cfg.add_section('Buttons')
    cfg.set('Buttons', 'size_x', '40')
    cfg.set('Buttons', 'size_y', '40')
    cfg.add_section('Treeview')
    cfg.set('Treeview', 'columns', 'Name,MEASURE.Sample,MEASURE.Date_of_measure')
    cfg.add_section('Log')
    cfg.set('Log', 'Height', '5')
    return cfg

@pytest.fixture
def gui_root():
    # Points to packages/HDF5_BLS_GUI
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def test_button_panel_signals(qtbot, config, gui_root):
    """Test that buttons in ButtonPanel emit signals when clicked."""
    panel = ButtonPanel(config, gui_root)
    qtbot.add_widget(panel)
    
    # Verify buttons dict exists
    assert hasattr(panel, 'buttons')
    assert 'new' in panel.buttons
    
    with qtbot.waitSignal(panel.new_requested):
        qtbot.mouseClick(panel.buttons['new'], Qt.LeftButton)

def test_architecture_widget_initialization(qtbot, config, gui_root):
    """Test that ArchitectureWidget initializes with its handler."""
    handler = HDF5Handler()
    widget = ArchitectureWidget(handler, config, gui_root)
    qtbot.add_widget(widget)
    
    assert widget.handler == handler
    # ArchitectureWidget is a QTreeView itself
    assert widget.model() is not None
