Using the *HDF5_BLS_analyse* module is done following these steps:

1. Create an object corresponding to the type of spectrometer
2. Define the algorithm to use to perform the analysis (either by creating it or by opening an existing one)
3. Perform the analysis
4. (optional) Save the algorithm to a JSON file

Example with a VIPA spectrometer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following example shows how to perform the analysis of a VIPA spectrometer. The code is written in Python and assumes that the *HDF5_BLS_analyse* module is installed.

.. code-block:: python

    from HDF5_BLS_analyse import Analyse_VIPA
    import numpy as np
    
    # Initialising the Analyse_VIPA object on the mock spectrum
    analyser = Analyse_VIPA(x = np.arange(mock_spectrum.size), y = mock_spectrum)
   
    # Creating a blank algorithm to perform the analysis
    analyser.silent_create_algorithm(algorithm_name="VIPA spectrum analyser", 
                                version="v0", 
                                author="Pierre Bouvet", 
                                description="This algorithm allows the user to recover a frequency axis basing ourselves on a single Brillouin spectrum obtained with a VIPA spectrometer. Considering that only one Brillouin Stokes and anti-Stokes doublet is visible on the spectrum, the user can select the peaks he sees, and then perform a quadratic interpolation to obtain the frequency axis. This interpolation is obtained either by entering a value for the Brillouin shift of the material or by entering the value of the Free Spectral Range (FSR) of the spectrometer. The user can finally recenter the spectrum either using the average between a Stokes and an anti-Stokes peak or by choosing an elastic peak as zero frequency.")
    
    # Adding points corresponding to peaks to the algorithm
    analyser.add_point(position_center_window=12, type_pnt="Elastic", window_width=5)
    analyser.add_point(position_center_window=37, type_pnt="Anti-Stokes", window_width=5)
    analyser.add_point(position_center_window=236, type_pnt="Stokes", window_width=5)
    analyser.add_point(position_center_window=259, type_pnt="Elastic", window_width=5)
    analyser.add_point(position_center_window=282, type_pnt="Anti-Stokes", window_width=5)
    analyser.add_point(position_center_window=466, type_pnt="Stokes", window_width=5)
    analyser.add_point(position_center_window=488, type_pnt="Elastic", window_width=5)
    analyser.add_point(position_center_window=509, type_pnt="Anti-Stokes", window_width=5)

    # Defining the FSR of the VIPA used
    analyser.interpolate_elastic_inelastic(FSR = 60)

    # Identifying the central peaks and recentering the spectrum to have them be symetric
    analyser.add_point(position_center_window=57, type_pnt="Stokes", window_width=1)
    analyser.add_point(position_center_window=68.5, type_pnt="Anti-Stokes", window_width=1)
    analyser.center_x_axis(center_type = "Inelastic")

    # Saving the algorithm to a standalone JSON file
    analyser.silent_save_algorithm(filepath = "algorithms/Analysis/VIPA spectrometer/Test.json", save_parameters=True)

    # Extracting the PSD and frequency axis from the analyser object
    frequency = analyser.x
    PSD = analyser.y