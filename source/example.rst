Examples
========

Here we provide simple examples of use of the library.

Creation of HDF5 file from raw data
------------------

If a file *"example.dat"* obtained with the GHOST software has to be imported, these are the commands we can use:

.. code:: python
   :number-lines:

   from HDF5_BLS import HDF5_BLS

   # Initialize the HDF5_BLS object
   bls = HDF5_BLS()

   # Open raw data from a .DAT file and store it in the object
   bls.open_data("example.DAT")

   # Save the data, abscissa, and metadata attributes to an HDF5 file
   bls.save_hdf5_as("output_data.h5")


Adding properties to the hdf5 file
------------------

Supposing that we want to add different properties to the data we are converting (the sample we were looking at, the wavelength, ...), then we can use the following code to add our properties to the file we had and save it again.

.. code:: python
   :number-lines:

   # Add metadata attributes describing the measurement and spectrometer settings
   bls.properties_data(
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
   bls.save_hdf5_as("output_data.h5")

Adding abscissa to the data
------------------

If we now look at a ranges of measures where we monitor a physical evolution and assess the changes in the BLS spectra. We can input the abscissa in our HDF5 file either by specifying the ranges we were looking at (for example if we were moving the sample at a constant speed during measure):

.. code:: python
   :number-lines:

   # Define an abscissa for the data
   bls.define_abscissa(min_val=0, max_val=100, nb_samples=1000)

Or just open the file containing the independent measures (for example a measure of temperature in a sample):

.. code:: python
   :number-lines:

   # Load an abscissa file for the data
   bls.import_abscissa("values.dat")

Adding calibration curves and impulse responses to the data
--------

We can also add to the HDF5 file calibration curves and impulse responses that can be used in the treatment phase to deconvolve the instrument response or obtain a frequency axis (in a VIPA spectrometer for example).

.. code:: python
   :number-lines:
   
   # Load and add a calibration curve from a .DAT file (optional)
   bls.open_calibration("calibration_curve.dat")

   # Load and add an impulse response curve (optional)
   bls.open_IR("impulse_response.dat")

   
