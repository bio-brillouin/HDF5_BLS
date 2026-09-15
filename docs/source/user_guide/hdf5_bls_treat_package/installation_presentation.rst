.. _hdf5_bls_treat_package_installation:

Installation
^^^^^^^^^^^^
To install the package, you can either:
* Download the source code from the GitHub repository (the hard way) 
* Use pip to install the package (the easy way) 

With pip
""""""""

To install the HDF5_BLS library to use in Python scripts or Jupyter notebooks, you can use pip:

.. code-block:: bash

    pip install HDF5_BLS_treat

This will install the latest version of the package from the Python Package Index (PyPI).

.. attention::
    This allows you to install the HDF5_BLS_treat library but not the HDF5_BLS (see :ref:`hdf5_bls_package_installation`) and HDF5_BLS_analyse libraries that have to be installed separately. This installation also does not allow you to run the GUI. To use the GUI, please download the entire `GitHub repository <https://github.com/bio-brillouin/HDF5_BLS>`__ and run the GUI from source.

From source
"""""""""""

The source code can be downloaded from the `GitHub repository <https://github.com/bio-brillouin/HDF5_BLS>`__. To download the source code, click on the green button "Code" and then click on the "Download ZIP" button. Once the download is complete, unzip the file and open a terminal in the unzipepd file. To install the package, run the following command:

.. code-block:: bash

    pip install packages/HDF5_BLS_treat

This will install the package and all its dependencies. To check if the package was installed correctly, run the following command:

.. code-block:: bash

    python -c "import HDF5_BLS_treat"

If the package was installed correctly, the command will not return any error.

If you want to contribute to the development of the project, we recommend you to check the :ref:`developer_setup_vscode` section of the documentation where we explain how to set up your development environment on Visual Studio Code and install the package in editable mode.

.. _hdf5_bls_treat_package_presentation:

Presentation
^^^^^^^^^^^^

The *HDF5_BLS_treat* package is a standalone module designed to process and fit Power Spectral Density (PSD) data for Brillouin Light Scattering (BLS) experiments. It provides a robust framework for defining lineshape models, managing data treatment history, and performing batch processing on large datasets. It also integrates an error estimator for the fitting performs that is returned as a statistically meaningful standard deviation (or variance) on the returned results.

Here is an example of code performing a simple treatment:

.. code-block:: python

    from HDF5_BLS_treat import Treat
    import numpy as np
    
    # Initialising the Treat object on the a doublet of frequency and PSD
    treat = Treat(frequency = frequency, PSD = data)
   
    # Creating a blank algorithm to perform the analysis
    treat.silent_create_algorithm(algorithm_name="VIPA spectrum analyser", 
                            version="v0", 
                            author="Pierre Bouvet", 
                            description="This algorithm allows the user to recover a frequency axis basing ourselves on a single Brillouin spectrum obtained with a VIPA spectrometer. Considering that only one Brillouin Stokes and anti-Stokes doublet is visible on the spectrum, the user can select the peaks he sees, and then perform a quadratic interpolation to obtain the frequency axis. This interpolation is obtained either by entering a value for the Brillouin shift of the material or by entering the value of the Free Spectral Range (FSR) of the spectrometer. The user can finally recenter the spectrum either using the average between a Stokes and an anti-Stokes peak or by choosing an elastic peak as zero frequency.")
    
    # Adding points corresponding to the central peaks to the algorithm so as to normalize the PSD
    treat.add_point(position_center_window=-6, type_pnt="Anti-Stokes", window_width=5)
    treat.add_point(position_center_window=6, type_pnt="Stokes", window_width=5)
    treat.normalize_data(threshold_noise = 0.05)

    # Adding the peaks to fit
    treat.add_point(position_center_window=-6, type_pnt="Anti-Stokes", window_width=5)
    treat.add_point(position_center_window=6, type_pnt="Stokes", window_width=5)

    # Defining the model for fitting the peaks
    treat.define_model(model="DHO", elastic_correction=False) 

    # Estimating the linewidth from selected peaks
    treat.estimate_width_inelastic_peaks(max_width_guess=5)

    # Fitting all the selected inelastic peaks with multiple peaks fitting
    treat.single_fit_all_inelastic(guess_offset=True, 
                                   update_point_position=True, 
                                   bound_shift=[[-7, -5], [5, 7]], 
                                   bound_linewidth=[[0, 5], [0, 5]])

    # Applying the algorithm to all the spectra (in the case where PSD is a 2D array)
    treat.apply_algorithm_on_all()

    # Combining the two fitted peaks together here weighing the result on the standard deviation of the shift
    treat.combine_results_FSR(FSR = 60, keep_max_amplitude = False, amplitude_weight = False, shift_err_weight= True)

    # Extracting the results
    shift = treat.shift
    linewidth = treat.linewidth
    amplitude = treat.amplitude
    BLT = treat.BLT
    shift_var = treat.shift_var
    linewidth_var = treat.linewidth_var
    amplitude_var = treat.amplitude_var 
    BLT_var = treat.BLT_var