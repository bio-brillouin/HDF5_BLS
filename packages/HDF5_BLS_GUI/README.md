# HDF5_BLS_GUI

Graphical User Interface (GUI) for the [HDF5_BLS](https://github.com/bio-brillouin/HDF5_BLS) project. This application provides a user-friendly way to explore, manage, and process Brillouin Light Scattering (BLS) data stored in HDF5 files.

## Features

- **HDF5 Architecture Explorer**: Visualize the hierarchical structure of your HDF5 files.
- **Data Properties Viewer**: Inspect normalized attributes (Measure, Spectrometer, etc.) for any selected dataset or group.
- **Drag-and-Drop Import**: Easily add data to your HDF5 files by dragging files onto the interface.
- **Integrated Processing**: Access analysis and treatment tools (`HDF5_BLS_analyse`, `HDF5_BLS_treat`) directly from the GUI (in development).
- **Data Management**: Create new files, open existing ones, repack data, and manage HDF5 groups/datasets.

## Installation

### From Source (Local Development)

To install the GUI in editable mode within your project environment:

```bash
pip install -e packages/HDF5_BLS_GUI
```

Ensure you have the core dependencies installed:
- `PySide6`
- `matplotlib`
- `HDF5_BLS`
- `HDF5_BLS_analyse`
- `HDF5_BLS_treat`

## Usage

You can launch the GUI using the following command:

```bash
python -m HDF5_BLS_GUI.app
```

Or, if installed as a script:

```bash
HDF5-BLS-GUI
```

## Testing

The GUI includes a comprehensive test suite using `pytest-qt`. To run the tests in headless mode (recommended for CI or remote environments):

```bash
QT_QPA_PLATFORM=offscreen python -m pytest packages/HDF5_BLS_GUI/tests
```

## Documentation

For more detailed information on the HDF5_BLS project, please refer to the [main documentation](https://hdf5-bls.readthedocs.io/en/latest/).
