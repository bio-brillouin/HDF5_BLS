.. HDF5_BLS_Documentation documentation master file, created by
   sphinx-quickstart on Fri Nov  8 14:38:29 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

HDF5_BLS documentation
======================

HDF5_BLS is a Python library for handling Brillouin Light Scattering (BLS) data and converting them into a standardized HDF5 format. The library provides functions to open raw data files, define and import abscissa, add metadata, and save the organized data in HDF5 files. The library is currently compatible with the following file formats:

* **.DAT** files: spectra returned by the GHOST software
* **.TIF** files: an image format that can be used to export 2D detector images.

Features
--------

* Load raw BLS data from .DAT and .TIF files
* Define or import abscissa values
* Add calibration and impulse response curves to the HDF5 file
* Attach metadata attributes for experimental setup and measurement details
* Save data and metadata to an HDF5 file for standardized storage

Download
--------

The library is conveniently stored on the Python Package Index and can be downloaded with this code:

.. code:: python
   :number-lines:

   pip install HDF5_BLS
   
Example
-------

Here we provide a simple example where we import a spectrum, define an abscissa for the adta, add properties, a calibration and impulse response curve and finally export everything into a HDF5 file. 

.. code:: python
   :number-lines:

   from HDF5_BLS import HDF5_BLS

   # Initialize the HDF5_BLS object
   bls = HDF5_BLS()

   # Open raw data from a .DAT file and store it in the object
   bls.open_data("example.DAT")

   # Define an abscissa for the data
   bls.define_abscissa(min_val=0, max_val=100, nb_samples=1000)

   # Add metadata attributes describing the measurement and spectrometer settings
   bls.properties_data(
      MEASURE_Sample="Water",
      MEASURE_Date="2024-11-06",
      MEASURE_Exposure=10,                  # in seconds
      MEASURE_Dimension=3,
      SPECTROMETER_Type="TFP",
      SPECTROMETER_Model="JRS-TFP2",
      SPECTROMETER_Wavelength=532.0,          # in nm
      SPECTROMETER_Illumination_Type="CW",
      SPECTROMETER_Spectral_Resolution=15.0,  # in MHz
   )

   # Load and add a calibration curve from a .DAT file (optional)
   bls.open_calibration("calibration_curve.dat")

   # Load and add an impulse response curve (optional)
   bls.open_IR("impulse_response.dat")

   # Save the data, abscissa, and metadata attributes to an HDF5 file
   bls.save_hdf5_as("output_data.h5")




.. toctree::
   :maxdepth: 2
   :caption: Contents:
