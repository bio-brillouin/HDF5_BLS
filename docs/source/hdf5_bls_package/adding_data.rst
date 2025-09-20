The addition of any type of data or attribute to the HDF5 file has been centralized in the *Wrapper.add\_ dictionary* method. This method is safe but complex and not user-friendly. Methods derived from this method are meant to simplify the process of adding data to the HDF5 file, specific to each type of data.

To add a single dataset to a group, we first need to specify the type of dataset we want to add, which are the following:

* "Abscissa\_...": An abscissa array for the measures where the dimensions on which the dataset applies are given after the underscore.
* "Amplitude": The dataset contains the values of the fitted amplitudes.
* "Amplitude\_err": The dataset contains the error of the fitted amplitudes.
* "BLT": The dataset contains the values of the fitted amplitudes.
* "BLT\_err": The dataset contains the error of the fitted amplitudes.
* "Frequency": A frequency array associated to the power spectral density
* "Linewidth": The dataset contains the values of the fitted linewidths.
* "Linewidth\_err": The dataset contains the error of the fitted linewidths. 
* "PSD": A power spectral density array
* "Raw\_data": The dataset containing the raw data obtained after a BLS experiment.
* "Shift": The dataset contains the values of the fitted frequency shifts.
* "Shift\_err": The dataset contains the error of the fitted frequency shifts.
* "Other": The dataset contains other data that will not be used by the library.

From there, the following functions are available to add the dataset to the HDF5 file:

* add\_raw\_data: To add raw data to a group
* add\_PSD: To add a PSD to a group
* add\_frequency: To add a frequency axis to a group
* add\_abscissa: To add an abscissa to a group
* add\_treated\_data: To add a shift, linewidth and their respective errors to a dedicated "Treatment" group
* add\_other: To add a shift, linewidth and their respective errors to a dedicated "Treatment" group


General approach to adding data to the HDF5 file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Adding a dataset to the file always come with three other pieces of information:

* Where to add the dataset in the file
* What to call the added dataset
* What is the type of the dataset we want to add

To add a dataset to the file, we'll therefore call type-specific functions with the data to add, the place where to add it and the name to give the dataset as arguments, following a code of line resembling:

.. code-block:: python

    wrp.add_raw_data(data = data,
                     parent_group = "Brillouin/Water spectrum", 
                     name = "Measure of the year")


This approach is the one used for
* *add\_raw\_data*
* *add\_PSD*
* *add\_frequency*
* *add\_other*

**Example**
Let's consider the following example: we have just initialized a wrapper object and want to add a spectrum obtained from our spectrometer. We have already converted this spectrum to a numpy array, and named it *data*. Now we want to add this data in a group called "Water spectrum" in the root group of the HDF5 file and call this raw data "Measure of the year". Then we will write:

.. code-block:: python

    wrp.add_raw_data(data = data,
                     parent_group = "Brillouin/Water spectrum", 
                     name = "Measure of the year")


Now let's say that we have analyzed this spectrum and obtained a PSD (stored in the variable "psd") and frequency array (stored in the variable "freq"). We want to add these two arrays in the same group, and call them "PSD" and "Frequency" respectively. We will write:

.. code-block:: python

    wrp.add_PSD(data = psd,
                parent_group = "Brillouin/Water spectrum", 
                name = "PSD")
    wrp.add_frequency(freq,
                      parent_group = "Brillouin/Water spectrum", 
                      name = "Frequency")

Exception 1: Adding treated data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Adding treated data differs slightly from adding individual datasets as we'll usually collect a number of different results to store. Therefore, instead of using different functions to store a shift or linewidth array, we have chosen to use a single function to add all the results of treatment, and create the group dedicated to storing the treatment results. As such, the function will have the following attributes:

* parent_group: The parent group where to store the data in the HDF5 file
* name_group: The name of the group that will contain the treatment results
* amplitude (optional): The amplitude array to add
* amplitude_err (optional): The error of the amplitude array
* blt (optional): The Loss Tangent array to add
* blt_err (optional): The error of the Loss Tangent array
* linewidth (optional): The linewidth array to add
* linewidth_err (optional): The error of the linewidth array
* shift(optional): The shift array to add
* shift_err (optional): The error of the shift array


**Example**

Let's consider the following example: we have treated our data and have obtained a shift array (shift), a linewidth array (linewidth) and their errors (shift\_err and linewidth\_err). We want to add these arrays in the same group as the PSD, that is the group "Test". The treated data are stored in a separate group nested in the "Test" group by the choices made while building the structure of the file. This is so the name of the treatment group can be chosen freely. Let's say that in this case, we have performed a non-negative matrix factorization (NnMF) on the data, and extracted the shift values closest to 5GHz. We will therefore call this treatment "NnMF - 5GHz". We will write:

.. code-block:: python

    wrp.add_treated_data(shift = shift,
                         linewidth = linewidth,
                         shift_err = shift_err,
                         linewidth_err = linewidth_err,
                         parent_group = "Brillouin/Test", 
                         name_group = "NnMF - 5GHz")

Exception 2: Adding an abscissa
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Adding abscissa also differs from the general case as we might want to add an abscissa array that is multi-dimensional and be able to know which dimensions of the PSD the abscissa correspomnds to. The *add\_abscissa* method therefore has the following attributes:

* parent_group: The parent group where to store the data in the HDF5 file
* name: The name of the abscissa to add
* unit: The unit of the axis
* dim_start: The first dimension of the abscissa array, by default 0
* dim_end: The last dimension of the abscissa array, by default the last number of dimension of the array


**Example**
Let's consider the following example: we have just initialized a wrapper object and want to add an abscissa axis corresponding to our measures that have been stored in the group "Brillouin/Temp". Say that this abscissa axis corresponds to temperature values, from 35 to 40 degrees and that there are 10 points in the axis. We will therefore call this abscissa axis "Temperature". We will write:

.. code-block:: python

    wrp.add_abscissa(data = np.linspace(35, 40, 10),
                    parent_group = "Brillouin/Temp", 
                    name = "Temperature",
                    unit = "C",
                    dim_start = 0,
                    dim_end = 1)

If you now want to use custom values for this axis, you can also specify them directly in the function call:

.. code-block:: python

    wrp.add_abscissa(data = data,
                    parent_group = "Brillouin/Temp", 
                    name = "Temperature",
                    unit = "C",
                    dim_start = 0,
                    dim_end = 1)

