.. _hdf5_bls_analyse_package_installation:

Installation
^^^^^^^^^^^^
To install the package, you can either:
* Download the source code from the GitHub repository (the hard way) 
* Use pip to install the package (the easy way) 

With pip
""""""""

To install the HDF5_BLS library to use in Python scripts or Jupyter notebooks, you can use pip:

.. code-block:: bash

    pip install HDF5_BLS_analyse

This will install the latest version of the package from the Python Package Index (PyPI).

.. attention::
    This allows you to install the HDF5_BLS_analyse library but not the HDF5_BLS (see :ref:`hdf5_bls_package_installation`) and HDF5_BLS_treat libraries that have to be installed separately. This installation also does not allow you to run the GUI. To use the GUI, please download the entire `GitHub repository <https://github.com/bio-brillouin/HDF5_BLS>`__ and run the GUI from source.

From source
"""""""""""

The source code can be downloaded from the `GitHub repository <https://github.com/bio-brillouin/HDF5_BLS>`__. To download the source code, click on the green button "Code" and then click on the "Download ZIP" button. Once the download is complete, unzip the file and open a terminal in the unzipepd file. To install the package, run the following command:

.. code-block:: bash

    pip install packages/HDF5_BLS_analyse

This will install the package and all its dependencies. To check if the package was installed correctly, run the following command:

.. code-block:: bash

    python -c "import HDF5_BLS_analyse"

If the package was installed correctly, the command will not return any error.

If you want to contribute to the development of the project, we recommend you to check the :ref:`developer_setup_vscode` section of the documentation where we explain how to set up your development environment on Visual Studio Code and install the package in editable mode.

.. _hdf5_bls_analyse_package_presentation:

Presentation
^^^^^^^^^^^^

The HDF5_BLS_analyse library is a Python package meant to, given a spectrometer, extract in a unified way from data obtained by a spectrometer, the power spectral density (PSD) and the frequency axis. This package is designed to allow the user to create modular algorithms to perform the analysis. 

Here is an example of code performing a simple analysis of a spectrum obtained with a VIPA spectrometer:

.. code-block:: python

    ###############################################################################
    # Existing imports
    ###############################################################################
    from HDF5_BLS_analyse import Analyse_VIPA

    # Consider an array containing 50x50 interference spectra collected with a VIPA spectrometer (for example when a 2D mapping is performed)
    raw_data = np.random.random((50, 50, 512))

    # Create an object corresponding to the VIPA spectrometer
    analyser = Analyse_VIPA(x = frequency, y = PSD)

    # Create an algorithm to perform the analysis
    analyser.silent_create_algorithm(algorithm_name="VIPA spectrum analyser", 
                               version="v0", 
                               author="Pierre Bouvet", 
                               description="This algorithm allows the user to recover a frequency axis basing ourselves on a single Brillouin spectrum obtained with a VIPA spectrometer. Considering that only one Brillouin Stokes and anti-Stokes doublet is visible on the spectrum, the user can select the peaks he sees, and then perform a quadratic interpolation to obtain the frequency axis. This interpolation is obtained either by entering a value for the Brillouin shift of the material or by entering the value of the Free Spectral Range (FSR) of the spectrometer. The user can finally recenter the spectrum either using the average between a Stokes and an anti-Stokes peak or by choosing an elastic peak as zero frequency.")

    analyser.add_point(position_center_window=12, type_pnt="Elastic", window_width=5)
    analyser.add_point(position_center_window=37, type_pnt="Anti-Stokes", window_width=5)
    analyser.add_point(position_center_window=236, type_pnt="Stokes", window_width=5)
    analyser.add_point(position_center_window=259, type_pnt="Elastic", window_width=5)
    analyser.add_point(position_center_window=282, type_pnt="Anti-Stokes", window_width=5)
    analyser.add_point(position_center_window=466, type_pnt="Stokes", window_width=5)
    analyser.add_point(position_center_window=488, type_pnt="Elastic", window_width=5)
    analyser.add_point(position_center_window=509, type_pnt="Anti-Stokes", window_width=5)
    
    analyser.interpolate_elastic_inelastic(FSR = 60)
    
    analyser.add_point(position_center_window=57, type_pnt="Stokes", window_width=1)
    analyser.add_point(position_center_window=68.5, type_pnt="Anti-Stokes", window_width=1)
    analyser.center_x_axis(center_type = "Inelastic")

    analyser.silent_save_algorithm(filepath = "algorithms/Analysis/VIPA spectrometer/Test.json", save_parameters=True)
    
    analyser.silent_open_algorithm(filepath = "algorithms/Analysis/VIPA spectrometer/MUW_PB_VIPA_FSR_Shift_v0.json")
    analyser.silent_run_algorithm()
    
.. admonition:: Unification

    This package also aims at unifying all the processing steps to extract PSD from raw data and extract Brillouin shift and linewidth from the PSD. These unifying steps are however not necessary to store your data in an HDF5 file. We will describe later the solution we propose to do this.
