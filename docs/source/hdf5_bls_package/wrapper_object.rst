The "wrapper" module has one main object: *Wrapper*. This object is used to interact with the HDF5 file. It is used to read the data, to write the data and to modify any aspect of the HDF5 file (dataset, groups or attributes). The module also provides different error objects used to recognize errors when using the Wrapper object and raise exceptions.

The Wrapper object is initialized by running the following command:

.. code-block:: python

    wrp = Wrapper()

This line creates a new Wrapper object with no attributes or data. It also creates a temporary H5 file stored in the temporary directory of the OS, with the following structure:

.. code-block:: bash

    file.h5
     └── Brillouin (group)

By default, the attributes of the "Brillouin" group are the following:

.. code-block:: bash

    file.h5
    └── Brillouin (group)
        ├── Brillouin_type -> "Root"
        └── HDF5_BLS_version -> "0.1" # The current of the HDF5_BLS package (might be updated in the future)

.. admonition:: Important

    As long as no filepaths are given to the Wrapper object, the file is stored in a temporary folder (the temporary folder of the operating system). Note that this temporary file is deleted either when the Wrapper object is destroyed or when the file is stored elsewhere. It is therefore good practice to specify a non-temporary filepath to the file when creating a new Wrapper object, with the "filepath" parameter:    

    .. code-block:: python

        wrp = Wrapper(filepath = "path/to/file.h5")

    Alternatively, you can save the file with the "save_as_hdf5" method of the Wrapper object. This method copies the current file to the given filepath and deletes the H5 file if it was temporary:

    .. code-block:: python

        wrp = Wrapper()
        wrp.save_as_hdf5(filepath = "path/to/file.h5")
    

To open an existing H5 file, you can directly give the path to the file to the Wrapper object:

.. code-block:: python

    wrp = Wrapper(filepath = "path/to/file.h5")
