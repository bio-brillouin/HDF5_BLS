.. _gui_quickstart:

Quickstart
==========

Introduction
------------

The HDF5_BLS GUI is a graphical user interface for the HDF5_BLS library. It allows users to create, open, and manage HDF5 files with a Brillouin group as defined in the HDF5_BLS package in a user-friendly way.

Layout of the GUI
^^^^^^^^^^^^^^^^^

The main window of the HDF5_BLS GUI is divided into three main parts:

1. The **Architecture Tree** (left panel): This panel displays the hierarchical structure of the Brillouin group of the HDF5 file. Users can navigate through the tree to select specific groups or datasets, edit the structure, rename elements, delete elements, ...
2. The **Properties Tab** (right panel): This panel displays the properties of the selected element in the Architecture Tree. Users can view and edit the attributes of the selected element, but also have a quick visualization of the data stored in the element.
3. The **Tools Menu** (top menu bar): This menu bar provides some tools for managing the HDF5 file.

.. figure:: _static/gui/main_window_empty.png
   :alt: Main window of the HDF5_BLS GUI

Interaction with elements in the GUI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The GUI is meant to act as a proxy to the file viewer of your OS, but with tools specific to the HDF5_BLS project. Therefore, to interact with the elements of the HDF5 file, just as on your OS, you can either:

- Right-click on an element to open a context menu
- Drag and drop elements to move them inside the file, to import elements to the file and to export elements from the file
- Use the menubar on elements 

Creating a new HDF5 file
------------------------

To create a new HDF5 file, click on the "New" button in the menubar.
.. figure:: _static/gui/new_hdf5_file.png
   :alt: Button to create a new HDF5 file

.. note::
    You can also create a new HDF5 file by clicking on the "File" menu and selecting "New file".


.. note::
    You can also create a new HDF5 file by using the "Ctrl+N" (Windows/Linux) or "Cmd+N" (macOS) keyboard shortcut.

.. important::
    The new HDF5 file is created in a temporary directory, you need to save it to a permanent location to keep it, else it will be deleted when the GUI is closed.

Opening an existing HDF5 file
-----------------------------

To open an existing HDF5 file, click on the "Open" button in the menubar.
.. figure:: _static/gui/open_hdf5_file.png
   :alt: Button to open an HDF5 file

.. note::
    You can also drag and drop an HDF5 file onto the architecture (left) panel to open it.

.. note::
    You can also open an HDF5 file by clicking on the "File" menu and selecting "Open file".


.. note::
    You can also open an HDF5 file by using the "Ctrl+O" (Windows/Linux) or "Cmd+O" (macOS) keyboard shortcut.

Editing a HDF5 file
-------------------

To edit an existing HDF5 file, click on one of its elements in the architecture (left) panel. Then by left clicking on the element, you will find a number of options in the context menu. You will also notice that the property (right) panel of the GUI has been updated to show the properties of the selected element. These properties can directly be edited in the GUI, you can also click the "Edit Attributes" button on the property panel to open the Attribute Editor window.

.. figure:: _static/gui/context_menu_element_architecture_frame.png
   :alt: Context menu of an element in the architecture frame