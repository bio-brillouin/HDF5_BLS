Using the *HDF5_BLS_treat* module is done following these steps:

1. Create an object corresponding to the type of spectrometer
2. Define the algorithm to use to perform the analysis (either by creating it or by opening an existing one)
3. Perform the analysis
4. (optional) Save the algorithm to a JSON file

Example
^^^^^^^

The following example shows how to perform a simple fit of a Stokes and an Anti-Stokes peak in a PSD.

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