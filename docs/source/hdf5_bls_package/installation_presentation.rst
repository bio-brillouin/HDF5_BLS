
Installation
^^^^^^^^^^^^
To install the package, you can either:
* Download the source code from the GitHub repository (the hard way) 
* Use pip to install the package (easy way) 

**Using pip**

To install the package using pip, run the following command:

.. code-block:: bash

    pip install HDF5_BLS

This will install the latest version of the package from the Python Package Index (PyPI).

**Downloading the source code**

The source code can be downloaded from the `GitHub repository <https://github.com/bio-brillouin/HDF5_BLS>`__. To download the source code, click on the green button "Code" and then click on the "Download ZIP" button. Once the download is complete, unzip the file and open a terminal in the folder where the code is stored. To install the package, run the following command:

.. code-block:: bash

    python setup.py install

This will install the package and all its dependencies. To check if the package was installed correctly, run the following command:

.. code-block:: bash

    python -c "import HDF5_BLS"

If the package was installed correctly, the command will not return any error.

This option is especially useful if you want to contribute to the package, as you can also clone the repository, and then use pip to install the package in editable mode. This will allow you to make changes or update the package from Git without having to reinstall the package every time.

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

Module structure
^^^^^^^^^^^^^^^^

The HDF5\_BLS package is built around the following different modules:

* *wrapper*: This module is used to interact with HDF5 files. It is used to read the data, to write the data and to modify any aspect of the HDF5 file (dataset, groups or attributes).
* *analyze*: This module is used to convert raw data taken from a spectrometer into a physically meaningful Power Spectral Density (PSD) array. This process is done to be reliable 
* *treat*: This module is used to extract information from the PSD array, such as the frequency shift and line width of the spectral lines. Note that this module has been made independent of the wrapper module and can be installed separately under the name of HDF5\_BLS\_treat.
* *load\_data*: This module is used to import data from any formats of interest. This module is an interface between physical files stored on the PC and the wrapper module. It has been designed to be easily extended to any format of data.
