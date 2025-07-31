.. HDF5_BLS documentation master file, created by
   sphinx-quickstart on Wed Jan  8 12:55:51 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to HDF5_BLS's documentation!
====================================

The `HDF5_BLS` project is a Python package allowing users to easily store Brillouin Light Scattering relevant data in a single HDF5 file. The package is designed to integrate in existing Python workflows and to be as easy to use as possible. 

Quick Start
-----------

Installation
~~~~~~~~~~~~

To install the package, you can use pip:

.. code-block:: bash
   
   pip install HDF5_BLS

Usage
~~~~~

Integration to workflow
^^^^^^^^^^^^^^^^^^^^^^^

Once the package is installed, you can use it in your Python scripts as follows:

.. code-block:: python
   
   import HDF5_BLS as bls
   
   # Create a HDF5 file
   wrp = bls.Wrapper(filepath = "path/to/file.h5")
   
   ###############################################################################
   # Existing code to extract data from a file
   ###############################################################################
   # Storing the data in the HDF5 file (for this example we use a random array)
   data = np.random.random((50, 50, 512))
   wrp.add_raw_data(data = data, parent_group = "Brillouin", name = "Raw data")
   
   ###############################################################################
   # Existing code to convert the data to a PSD
   ###############################################################################
   # Storing the Power Spectral Density in the HDF5 file together with the associated frequency array (for this example we use random arrays)
   PSD = np.random.random((50, 50, 512))
   frequency = np.arange(512)
   wrp.add_PSD(data = PSD, parent_group = "Brillouin", name = "Power Spectral Density")
   wrp.add_frequency(data = frequency, parent_group = "Brillouin", name = "Frequency")

   ###############################################################################
   # Existing code to fit the PSD to extract shift and linewidth arrays
   ###############################################################################
   # Storing the Power Spectral Density in the HDF5 file together with the associated frequency array (for this example we use random arrays)
   shift = np.random.random((50, 50))
   linewidth = np.random.random((50, 50))
   wrp.add_treated_data(parent_group = "Brillouin", name_group = "Treat_0", shift = shift, linewidth = linewidth)

Extracting the data from the HDF5 file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once the data is stored in the HDF5 file, you can extract it as follows:

.. code-block:: python
   
   import HDF5_BLS as bls
   
   # Open the file
   wrp = bls.Wrapper(filepath = "path/to/file.h5")

   # Extract the data
   data = wrp["Brillouin/path/in/file/Raw data"]

Contents:
---------

- `Modules <modules.html>`_ 

.. toctree::
   :maxdepth: 3
   :caption: Contents:
   
   source/modules
   

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
