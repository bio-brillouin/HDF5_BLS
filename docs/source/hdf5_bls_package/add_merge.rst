Creating a new HDF5 file based on two existing ones can be done one of two ways depending on the desired end result.

* The *\_\_add\_\_* dunder metthod. If we want to combine two HDF5 files into a single one "plainly", for example if we are generating a new HDF5 after each measure, with this structure:
    
    .. code-block:: bash

        20250214_HVEC_03.h5
        └──Brillouin (group)
            └── 20250214_HVEC_02
                └── Measure (dataset)

    and we already have a HDF5 file containing the data of the previous experiment:
    
    .. code-block:: bash

        20250214_HVEC.h5
        └── Brillouin (group)
            ├── 20250214_HVEC_01
            │   └── Measure (dataset)
            └── 20250214_HVEC_02
                └── Measure (dataset)

    We can simply add the first HDF5 file to the second one with:

    .. code-block:: python

        wrp1 = Wrapper(filepath = ".../20250214_HVEC.h5")
        wrp2 = Wrapper(filepath = ".../20250214_HVEC_02.h5")
        wrp = wrp1 + wrp2

    This will create a new HDF5 file with the following structure:
    
    .. code-block:: bash

        20250214_HVEC.h5
        └── Brillouin (group)
            ├── 20250214_HVEC_01
            │   └── Measure (dataset)
            ├── 20250214_HVEC_02
            │   └── Measure (dataset)
            └── 20250214_HVEC_03
                └── Measure (dataset)

    **WARNING:** The new file is a temporary file, it is therefore important to save it after the addition of the two files with:

    .. code-block:: python

        wrp.save_as_hdf5(filepath = wrp.filepath)

    Note that from there, wrp1 and wrp will be the same as the wrapper does not store any data in memory but just acts as an access facilitator to the file.

* The *add\_hdf5* method. If we want to import the HDF5 as a new group, for example if we have this HDF5 file containing the data of a cell study:
    
    .. code-block:: bash

        Neuronal_cell_study.h5
        └── Brillouin (group)
            ├── Neuronal (group)
            │   ├── GT 1-7 (group)
            │   │   └── ...
            │   ├── L-fibroblast (group)
            │   │   └── ...
            └── Skeletal (group)
                └── ...

    And we want to import data done on another neuronal cell line, say "MOV", that have been stored in the following HDF5 file:

    .. code-block:: bash

        MOV.h5
        └── Brillouin (group)
            └── MOV (group)
                └── ...

    We can simply add the second HDF5 file to the first one by specifying the path to the second file in the *Wrapper.add\_hdf5* method:

    .. code-block:: python

        wrp1 = Wrapper(filepath = ".../Neuronal_cell_study.h5")
        wrp1.add_hdf5(filepath = ".../MOV.h5", parent_group = "Brillouin/Neuronal")

    This will create a new HDF5 file with the following structure:

    .. code-block:: bash

        Neuronal_cell_study.h5
        └── Brillouin (group)
            ├── Neuronal (group)
            │   ├── GT 1-7 (group)
            │   │   └── ...
            │   ├── L-fibroblast (group)
            │   │   └── ...
            │   ├── MOV (group)
            │   │   └── ...
            └── Skeletal (group)
                └── ...
         