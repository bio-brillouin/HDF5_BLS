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
   




.. toctree::
   :maxdepth: 2
   :caption: Contents:
