Examples
========

Here we provide simple examples of use of the library.

Creation of HDF5 file from raw data
-----------------------------------

If a file *"example.dat"* obtained with the GHOST software has to be imported, these are the commands we can use:

.. code:: python
   :number-lines:

   from HDF5_BLS import Wraper

   # Initialize the HDF5_BLS object
   wrp = Wraper()

   # Open raw data from a .DAT file and store it in the object
   wrp.open_data("example.DAT")

   # Save the data, abscissa, and metadata attributes to an HDF5 file
   wrp.save_hdf5_as("output_data.h5")


Adding properties to the hdf5 file
----------------------------------

Supposing that we want to add different properties to the data we are converting (the sample we were looking at, the wavelength, ...), then we can use the following code to add our properties to the file we had and save it again.

.. code:: python
   :number-lines:

   # Add metadata attributes describing the measurement and spectrometer settings
   wrp.properties_data(
      MEASURE_Sample="Water",
      MEASURE_Date="2024-11-06",
      MEASURE_Exposure=10,                  # in seconds
      MEASURE_Dimension=3,
      SPECTROMETER_Type="TFP",
      SPECTROMETER_Model="JRS-TFP2",
      SPECTROMETER_Wavelength=532.0,          # in nm
      SPECTROMETER_Illumination_Type="CW",
      SPECTROMETER_Spectral_Resolution=15.0,  # in MHz
   )

   # Save the data, abscissa, and metadata attributes to an HDF5 file
   wrp.save_hdf5_as("output_data.h5")

Adding abscissa to the data
---------------------------

If we now look at a ranges of measures where we monitor a physical evolution and assess the changes in the BLS spectra. We can input the abscissa in our HDF5 file either by specifying the ranges we were looking at (for example if we were moving the sample at a constant speed during measure):

.. code:: python
   :number-lines:

   # Define an abscissa for the data
   wrp.define_frequency_1D(min_val=0, max_val=100, nb_samples=1000)

Or just open the file containing the independent measures (for example a measure of temperature in a sample):

.. code:: python
   :number-lines:

   # Load an abscissa file for the data
   wrp.import_frequency("values.dat")

Adding calibration curves and impulse responses to the data
-----------------------------------------------------------

We can also add to the HDF5 file calibration curves and impulse responses that can be used in the treatment phase to deconvolve the instrument response or obtain a frequency axis (in a VIPA spectrometer for example).

.. code:: python
   :number-lines:
   
   # Load and add a calibration curve from a .DAT file (optional)
   wrp.open_calibration("calibration_curve.dat")

   # Load and add an impulse response curve (optional)
   wrp.open_IR("impulse_response.dat")


Treating a spectrum 
-------------------

When the data have been opened, it is possible to treat them with the "Treat" module

.. code:: python
   :number-lines:

   from HDF5_BLS import Treat

   treat = Treat()

   opt, std = treat.fit_model(wrp.frequency, # The frequency axis of the data
                              wrp.data, # The data
                              7.43, # The estimated shift position
                              1, # The estimated linewidth
                              normalize = True, # A parameter to normalize peaks beofre fitting them
                              model = "Lorentz", # The choice of the model (in this case, a Lorentzian lineshape)
                              fit_S_and_AS = True, # Fitting will be performed on both the Stokes and anti-Stokes peaks
                              window_peak_find = 1, # The window in GHz where to find the peaks
                              window_peak_fit = 3, # The window in GHz in which to fit the peaks
                              correct_elastic = True, # A parameter to correct for the influence of the elastic peak on the signal
                              IR_wndw = [-0.5,0.5]) # The position of the elastic peak on the spectrum, used as the impulse response function of the instrument

This code will return the result of the fit (in the presented case, a Lorentzian lineshape) together with the standard deviation on the fitted parameters.
Note that all the steps performed during this treatment can be reviewed by accessing the dedicated list:

.. code:: python
   :number-lines:

   treat.steps

Note also that any errors during treatment will result in a TreatmentError with a description of the error for debugging.