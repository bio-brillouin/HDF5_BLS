
Installation
^^^^^^^^^^^^
To install the package, you can either download the source code from the GitHub repository or use pip to install the package. We recommend using pip for users who do not intend on working on the package as it is the easiest way to install the package.

**Using pip**

To install the package using pip, run the following command:

.. code-block:: bash

    pip install HDF5_BLS

**Downloading the source code**

The source code can be downloaded from the 'GitHub repository <https://github.com/bio-brillouin/HDF5_BLS>'__. To download the source code, click on the green button "Code" and then click on the "Download ZIP" button. Once the download is complete, unzip the file and open a terminal in the folder where the code is stored. To install the package, run the following command:

.. code-block:: bash

    python setup.py install

This will install the package and all its dependencies. To check if the package was installed correctly, run the following command:

.. code-block:: bash

    python -c "import HDF5_BLS"

If the package was installed correctly, the command will not return any error.

Presentation
^^^^^^^^^^^^

The HDF5\_BLS library is a Python package meant to interface Python code with a HDF5 file.

The goal of this package is to allow the user to semalessly integrate the proposed standard to their existing code. A detailed description of the package will be given in the later sections of this tutorial. Here is however a quick code example to show the integration of the package in a simple case:

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

This package also aims at unifying both the way to extract PSD from raw data and extract Brillouin shift and linewidth from the PSD. We will describe later how to do this, we encourage interested readers to already try and add the above code to their code and see how it works. 

Module structure
^^^^^^^^^^^^^^^^

The HDF5\_BLS package is built around the following different modules:

* *wrapper*: This module is used to interact with HDF5 files. It is used to read the data, to write the data and to modify any aspect of the HDF5 file (dataset, groups or attributes).
* *analyze*: This module is used to convert raw data taken from a spectrometer into a physically meaningful Power Spectral Density (PSD) array. This process is done to be reliable 
* *treat*: This module is used to extract information from the PSD array, such as the frequency shift and line width of the spectral lines. 
* *load\_data*: This module is used to import data from any formats of interest. This module is an interface between physical files stored on the PC and the wrapper module. It has been designed to be easily extended to any format of data.
