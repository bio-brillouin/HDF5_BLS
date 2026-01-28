HDF5_BLS Library: Comprehensive Researcher Tutorial
============================================================

This tutorial describes how to use the ``Wrapper`` object to manage Brillouin Light Scattering (BLS) data. The library enforces basic HDF5 organization to ensure data integrity across research teams.

1. Initialization: Starting a Session
======================================

The ``Wrapper`` object is your gateway to an HDF5 file.

**Methods:** ``__init__``, ``close``

.. code-block:: python

    from wrapper import Wrapper
    import numpy as np

    # Create a permanent file
    wrp = Wrapper("research_data.h5")

    # Create a temporary file
    wrp_temp = Wrapper()

**Outcome:**
* If the file is new, a root group named ``Brillouin`` is automatically created with the attribute ``Brillouin_type: Root``.
* **Temporary Files:** If no path is provided, a file is created in your OS temp folder. It exists only in memory/temp storage.

.. warning::
   **Closing the file:** Use ``wrp.close()``. If you are using a temporary file and have not moved it, the library will raise a ``WrapperError_Save`` to prevent accidental data loss. To discard a temp file, use ``wrp.close(delete_temp_file=True)``.

2. Organizing the Hierarchy
===========================

**Methods:** ``create_group``, ``change_name``, ``change_brillouin_type``, ``delete_element``

Researchers often need to create nested structures for different samples or processing steps.

.. code-block:: python

    # 1. Create a group for raw data
    wrp.create_group(name="Sample_A", parent_group="Brillouin", brillouin_type="Measure")

    # 2. Oops, it was actually a processed sample. Let's fix it.
    wrp.change_brillouin_type(path="Brillouin/Sample_A", brillouin_type="Treatment")

    # 3. Rename it for clarity
    wrp.change_name(path="Brillouin/Sample_A", name="Annealed_Sample_A")

**Outcome:**
The file structure evolves from ``/Brillouin`` to ``/Brillouin/Annealed_Sample_A``. The metadata of the group now correctly identifies it as a ``Treatment`` type.

.. note::
   **Deletion:** When you use ``wrp.delete_element("path/to/data")``, the data is removed, but HDF5 files do not shrink in size immediately. The library sets a ``need_for_repack`` flag. The file size will only shrink (repack) once ``wrp.close()`` is called.

3. Adding Data and Metadata
===========================

**Methods:** ``add_dictionary``, ``add_attribute``

The most robust way to add data is via a dictionary, which allows you to define the dataset and its attributes (like units or laser power) simultaneously.

.. code-block:: python

    # Mock data: A 5x5 map of 1024-point spectra
    spectra_data = np.random.random((5, 5, 1024))
    
    data_packet = {
        "PSD": {"Name": "Map_Data", "Data": spectra_data},
        "Attributes": {"Laser_Wavelength": "532nm"}
    }

    wrp.add_dictionary(data_packet, parent_group="Brillouin/Annealed_Sample_A")

    # Add a single attribute later
    wrp.add_attribute(path="Brillouin/Annealed_Sample_A", name="Humidity", value="45%")

**Outcome:**
A dataset is created at ``Brillouin/Annealed_Sample_A/Map_Data``. It contains the 3D array and is tagged as a ``PSD`` type. The parent group now contains metadata for wavelength and humidity.

4. Merging and Combining Data
=============================

**Methods:** ``add_hdf5``, ``combine_datasets``, ``__add__``

In research, you often need to merge results from multiple days or different setups.

Merging an external file (``add_hdf5``)
--------------------------------------
.. code-block:: python

    # Import 'experiment_day2.h5' into our current file
    wrp.add_hdf5("experiment_day2.h5", parent_group="Brillouin/Comparison")

**Outcome:**
Every group and dataset from the second file is copied into the ``Comparison`` folder of your current file.

Adding two Wrapper objects (``__add__``)
---------------------------------------
.. code-block:: python

    wrp1 = Wrapper("day1.h5")
    wrp2 = Wrapper("day2.h5")
    wrp3 = wrp1 + wrp2

**Outcome:**
A new temporary ``Wrapper`` (wrp3) is created. It contains two main groups under Root: ``day1`` and ``day2``. This is the fastest way to aggregate multiple experimental sessions into one workspace.

Combining Datasets (``combine_datasets``)
-----------------------------------------
.. code-block:: python

    # Combine two 1D spectra into a single 2D dataset
    wrp.combine_datasets(datasets=["Brillouin/S1/Spec1", "Brillouin/S1/Spec2"], 
                         parent_group="Brillouin/Combined", 
                         name="Total_Spectra")

**Outcome:**
If Spec1 and Spec2 were arrays of shape ``(1024,)``, the new dataset ``Total_Spectra`` will have a shape of ``(2, 1024)``.

5. Inspection and Visualization
===============================

**Methods:** ``print_structure``, ``print_metadata``, ``get_structure``, ``get_attributes``, ``__getitem__``

Before exporting, you should verify the file contents.

.. code-block:: python

    # Visual tree print
    wrp.print_structure()

    # Accessing data directly
    my_array = wrp["Brillouin/Annealed_Sample_A/Map_Data"]

**Outcome:**
The ``print_structure`` method outputs a text-based tree in your console, showing the names and ``Brillouin_type`` of every element, making it easy to spot structural errors.

6. Exporting for Publication
============================

**Methods:** ``export_dataset``, ``export_brim``

**Outcome:**
* **export_dataset:** Creates a ``.csv``, ``.xlsx``, or ``.npy`` file of a specific dataset. Useful for plotting in Origin or Prism.
* **export_brim:** Converts the HDF5 structure into a ``.brim`` file format, specifically used for legacy Brillouin analysis software.

.. code-block:: python

    wrp.export_dataset("Brillouin/Annealed_Sample_A/Map_Data", "output.csv", export_type=".csv")

7. Error Handling Reference
===========================

* **WrapperError_Overwrite:** Raised if you try to create a group or dataset with a name that already exists in that path.
    * *Fix:* Use ``overwrite=True`` in the method arguments.
* **WrapperError_StructureError:** Raised if you try to assign an invalid ``Brillouin_type`` (e.g., trying to set a Dataset as a "Root").
    * *Fix:* Check the list of valid types in Section 1.
* **WrapperError_Save:** Raised when closing a temporary file.
    * *Fix:* Decide if you want to delete it (``delete_temp_file=True``) or move it to a permanent path first.