"""
brimfile.converter
===================

This subpackage provides tools to convert between **brim** and **brimX** file
formats for Brillouin microscopy data.

Installation
---------------
To run the brimconverter module you need additional dependencies:

```bash
pip install "brimfile[converter]"
```

Main interfaces
---------------

1. **BrimConverter**
   High-level class to convert between brim (`.brim.zarr`, `.brim.zip`, etc.)
   and brimX (`.brimX.h5`) formats.

   Modes:
   - ``brim2brimX`` → Convert brim → brimX
   - ``brimX2brim`` → Convert brimX → brim

   Example::

       from brimfile.converter import BrimConverter

       # brim → brimX
       brim_filename = "file_in.brim.zarr"
       brimX_filename = "file_out.brimX.h5"
       converter = BrimConverter(brim_filename, brimX_filename, mode="brim2brimX", stop_at=2)
       converter.convert()

       # brimX → brim
       brimX_filename = "file_in.brimX.h5"
       brim_filename = "file_out.brim.zarr"
       converter = BrimConverter(brimX_filename, brim_filename, mode="brimX2brim")
       converter.convert()

2. **HDF5Flattener**
   Lower-level utility for *flattening brimX HDF5 files*.  
   It reshapes datasets (PSD, frequency, shift, linewidth, amplitude, etc.)
   into consistent arrays and extracts per-acquisition metadata.  

   Example::

       from brimfile.converter import HDF5Flattener

       flattener = HDF5Flattener()
       data = flattener.flatten("file_in.brim.h5")
       PSD = data["PSD"][0]
       freq = data["frequency"][0]
       metadata = data["metadata"][0]

--------------------
Classes
--------

- :class:`BrimConverter`
    Convert between brim and brimX file formats.
- :class:`HDF5Flattener`
    Flatten brimX (HDF5) files into arrays + metadata for reconstruction.

"""

from .brim_converter import BrimConverter
from .hdf5_flattener import HDF5Flattener

__all__ = ["BrimConverter", "HDF5Flattener"]
