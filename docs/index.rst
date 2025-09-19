.. HDF5_BLS documentation master file, created by
   sphinx-quickstart on Wed Jan  8 12:55:51 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to HDF5_BLS's documentation!
====================================

The `HDF5_BLS` project is a Python package allowing users to easily store Brillouin Light Scattering relevant data in a single HDF5 file. The package is designed to integrate in existing Python workflows and to be as easy to use as possible. The package is a solution for unifying the data storage of Brillouin Light Scattering experiments, with three main goals:
- Simplicity: Make it easy to store and retrieve data from a single file.
- Universality: Allow all modalities to be stored in a single file, while unifying the metadata associated to the data.
- Expandability: Allow the format to grow with the needs of the community.

Quick Start
-----------
Spirit of the project
~~~~~~~~~~~~~~~~~~~~~

The idea of the package is to provide a simple way to store and retrieve data relevant to Brillouin Light Scattering experiments together with the metadata associated to the data. The file we propose to use is the HDF5 file format (standing for "Hierarchical Data Format version 5"). The idea of this project is to use this file format to reproduce the structure of a filesystem within a single file, storing all files corresponding to a given expoeriment in a single "group". For example, a typical structure of the HDF5 file could be:

.. code-block:: bash
   
   file.h5
   └── Brillouin
       ├── Measure of water
       │   ├── Image of the power spectral density
       │   ├── Channels associated to the power spectral density
       │   ├── Results after data processing
       │   │   ├── Shift
       │   │   ├── Shift variance
       │   │   ├── Linewidth
       │   │   ├── Linewidth variance
       │   │   ├── Amplitude
       │   │   ├── Amplitude variance
       │   │   ├── ... 
       ├── Measure of methanol
       │   ├── ...
   
To allow this file format to be used with other modalities (e.g. electrophoresis assays to complement a Brillouin experiment), we propose to use a top-level group corresponding a minima to the modality (e.g. "Brillouin"). We also propose to add to each element of the HDF5 file, a "Brillouin_type" attribute that will allow to know the type of the element. For datasets, these types are:

- Raw_data: the raw data
- PSD: a power spectral density array
- Frequency: a frequency array associated to the power spectral density
- Abscissa_x: an abscissa array for the measures where the name is written after the underscore.
- Shift: the shift array obtained after the treatment
- Shift_err: the array of errors on the shift array obtained after the treatment
- Linewidth: the linewidth array obtained after the treatment
- Linewidth_err: the array of errors on the linewidth array obtained after the treatment
- Amplitude: the amplitude array obtained after the treatment
- Amplitude_err: the array of errors on the amplitude array obtained after the treatment
- BLT: the Loss Tangent array obtained after the treatment
- BLT_err: the array of errors on the Loss Tangent array obtained after the treatment

For groups, these types are:

- Calibration_spectrum: the calibration spectrum
- Impulse_response: the impulse response
- Measure: the measure
- Root: the root group
- Treatment: the treatment


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

.. toctree::
   :maxdepth: 3
   :caption: Contents:
   
   source/modules
   

API Reference
=============

.. autosummary::
   :toctree: _autosummary
   :recursive:

   HDF5_BLS
