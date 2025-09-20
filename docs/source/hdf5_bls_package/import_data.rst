Importing datasets to the HDF5 file from independent data files, through the HDF5\_BLS package, is always done following to successive steps:

1. Extracting the data and the metadata that can be extracted from the data files. This can be done using the *load\_data* module.
2. Adding the data and metadata to the HDF5 file. This is done using the *Wrapper.add\_dictionary* method.

To make the process more user friendly, we have developed a set of derived methods that are specific to each type of data that is to be added (Raw data, PSD, Frequency, Abscissa or treated data). 

In this section, we will present these methods. We encourage interested readers to refer to the chapter dedicated to the load\_data module for more information on the extraction of the data and the metadata.

General approach for importing data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Much like adding data from a script, we can import data from external files by using type-specific functions. These functions are:

* *Wrapper.import\_abscissa*: To import an abscissa array.
* *Wrapper.import\_frequency*: To import a frequency array.
* *Wrapper.import\_PSD*: To import a PSD array.
* *Wrapper.import\_raw\_data*: To import raw data.
* *Wrapper.import\_treated\_data*: To import the data arrays resulting from a treatment.

These function work a bit differently from the ones used to add data, as we might need parameters to extract the data from the file. Therefore, these functions have the following attributes:

* filepath: The filepath to the file to import the data from.
* parent_group: The parent group where to store the data in the HDF5 file.
* name: The name of the dataset to add.
* creator: An identifier of the creator of the file. This is used to differentiate different structures of files using the same format (for example .dat files).
* parameters: A dictionary containing the parameters that are needed to extract the data from the file. This is used to either access the data if it is somehow encoded or to interpret the data if a routine pipeline is used to obtain for example a PSD from a time-domain dataset
* reshape: The new shape of the array, by default None means that the shape is not changed
* overwrite: A parameter to indicate whether the dataset should be overwritten if it already exists, by default False - attributes are not overwritten. 
* *all the attributes corresponding to the type of data (abscissa, frequency, PSD, raw data, treated data)*

**Example**
Let's consider the following example: we have just initialized a wrapper object and want to import an abscissa axis corresponding to our measures that have been stored in a .npy file (for example if a Python routine has been used to impose conditions for the measure). In that case, the array can be interpreted without any parameters nor specification.

.. code-block:: python

    wrp.import_abscissa(filepath = "path/to/file.npy", parent_group = "Brillouin/Measure", creator = None, parameters = None, name = "Time", unit = "s", dim_start = 0, dim_end = 1, reshape = None, overwrite = False)