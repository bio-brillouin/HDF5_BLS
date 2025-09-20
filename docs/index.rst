.. HDF5_BLS documentation master file, created by
   sphinx-quickstart on Wed Jan  8 12:55:51 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to HDF5_BLS's documentation!
====================================
.. admonition:: About HDF5_BLS

   The `HDF5_BLS` project is a Python package allowing users to easily store Brillouin Light Scattering relevant data in a single HDF5 file. The package is designed to integrate in existing Python workflows and to be as easy to use as possible. The package is a solution for unifying the data storage of Brillouin Light Scattering experiments, with three main goals:

   - **Simplicity**: Make it easy to store and retrieve data from a single file.
   - **Universality**: Allow all modalities to be stored in a single file, while unifying the metadata associated to the data.
   - **Expandability**: Allow the format to grow with the needs of the community.


Contents:
---------

.. toctree::
   :maxdepth: 3
   
   source/quickstart
   source/file_format
   source/hdf5_bls_package
   

API
===

.. autosummary::
   :toctree: _autosummary
   :recursive:

   HDF5_BLS
