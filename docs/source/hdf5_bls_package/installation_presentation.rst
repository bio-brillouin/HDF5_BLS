.. _hdf5_bls_package_installation:

Installation
^^^^^^^^^^^^

To install the package, you can either:
* Download the source code from the GitHub repository (the hard way) 
* Use pip to install the package (easy way) 

With pip
""""""""

To install the HDF5_BLS library to use in Python scripts or Jupyter notebooks, you can use pip:

.. code-block:: bash

    pip install HDF5_BLS

This will install the latest version of the package from the Python Package Index (PyPI).

.. attention::
    This allows you to install the HDF5_BLS library but not the HDF5_BLS_analyse (see :ref:`hdf5_bls_analyse_package_installation`) and HDF5_BLS_treat libraries that have to be installed separately. This installation also does not allow you to run the GUI. To use the GUI, please download the entire `GitHub repository <https://github.com/bio-brillouin/HDF5_BLS>`__ and run the GUI from source.

From source
"""""""""""

The source code can be downloaded from the `GitHub repository <https://github.com/bio-brillouin/HDF5_BLS>`__. To download the source code, click on the green button "Code" and then click on the "Download ZIP" button. Once the download is complete, unzip the file and open a terminal in the unzipepd file. To install the package, run the following command:

.. code-block:: bash

    pip install packages/HDF5_BLS

This will install the package and all its dependencies. To check if the package was installed correctly, run the following command:

.. code-block:: bash

    python -c "import HDF5_BLS"

If the package was installed correctly, the command will not return any error.

If you want to contribute to the development of the project, we recommend you to check the :ref:`developer_setup_vscode` section of the documentation where we explain how to set up your development environment on Visual Studio Code and install the package in editable mode.

Presentation
^^^^^^^^^^^^

The HDF5\_BLS library is a Python package meant to interface Python code with a HDF5 file. The development of this solution was based on three main goals:
1. Simplicity: Make it easy to store and retrieve data from a single file.
2. Universality: Allow all modalities to be stored in a single file, while unifying the metadata associated to the data.
3. Expandability: Allow the format to grow with the needs of the community.

Practically, this means using this solution should be easy, intuitive and allow a seamless integration of the proposed standard to your existing code. Here is a quick code example to show the integration of the package in a simple case (you want to store a signal out of a spectrometer, its corresponding power spectral density, its frequency axis and its shift and linewidth arrays):

.. code-block:: python

    ###############################################################################
    # Existing imports
    ###############################################################################
    from HDF5_BLS import wrapper

    # Create a new file
    wrp = wrapper.Wrapper(filepath = "path/to/the/file.h5")

    ###############################################################################
    # Existing code extracting data from a file
    ###############################################################################

    # Store the data in the file 
    wrp.add_raw_data(data = data, parent_group = "Brillouin/path/in/the/file", name = "Name of the dataset")

    ###############################################################################
    # Existing code extracting a PSD and a frequency vector from the data
    ###############################################################################

    # Store the frequency vector together with the raw data
    wrp.add_frequency(data = frequnecy, parent_group = "Brillouin/path/in/the/file", name = "Frequency vector")

    # Store the PSD dataset together with the raw data
    wrp.add_PSD(data = PSD, parent_group = "Brillouin/path/in/the/file", name = "PSD")

    ###############################################################################
    # Existing code extracting the shift and linewidth of the data
    ###############################################################################

    # Store the PSD dataset together with the raw data
    wrp.add_treated_data(shift = shift, linewidth = linewidth, parent_group = "Brillouin/path/in/the/file", name = "PSD")

.. admonition:: Unification

    This package also aims at unifying all the processing steps to extract PSD from raw data and extract Brillouin shift and linewidth from the PSD. These unifying steps are however not necessary to store your data in an HDF5 file. We will describe later the solution we propose to do this.
