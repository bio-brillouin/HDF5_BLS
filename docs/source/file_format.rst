The file format
===============

Basic file structure
--------------------

This project aims at defining a standard for storing Brillouin Light Scattering measures and associated treatment in a HDF5 file.

HDF5 stands for "Hierarchical Data Format" and is a file format that allows the storage of data in a hierarchical structure. This structure allows to store data in a way that is both human and machine readable. The structure of the file is based on the following base structure, which corresponds to the structure of a file containing a single measure (*Measure*) where no parameters have been stored:

.. code-block:: bash

    file.h5
    └── Brillouin (group)
        ├── Measure (group)
            └── Measure (dataset)


The dimensionality of the dataset is free, there are therefore by design virtually no restrictions on the data that can be stored in this format.

The organization of the file is based on the following principles:

* The file is organized in groups and datasets, which allows to store data in a hierarchical structure.
* Only one dataset corresponding to a measure can be stored per group. 
* The groups are used to organize the file and store metadata and parameters related to the measure, and the datasets are used to store the actual data.

Meta-files
----------

The Hierarchical Data Format (HDF5) finds its interest in storage for our community, of different measures. These result in "meta-files" where data corresponding to different experiments can be found. The organization of such a file will follow a structure similar to this one:

.. code-block:: bash
    file.h5
    └── Brillouin (group)
        ├── RWPE1 organoids (group)
        │   ├── Morphogenesis day 1 (group)
        │   │   ├── Sample 1 (group)
        │   │   │   ├── Measure (dataset)
        │   │   ├── Sample 2 (group)
        │   │   ├── ...
        │   ├── Morphogenesis day 2 (group)
        |   ├── ...
        ├── H6C7 organoids (group)
        ├── ...

Although no rules are imposed on the way to organize the file, we propose to associate a hierarchical level to an hyperparameter that has been varied for the experiment. In the given example:

* The first hierarchical level is associated to the cell line that is observed
* The second hierarchical level is associated to the day of the experiment
* The third hierarchical level is associated to the sample that was measured

Note that the format does not impose any restriction on the names of the groups nor the measures. This choice allows you to create user-friendly files that can be opened with any software that can read HDF5 files (e.g. HDFView, HDFCompass, Fiji, H5Web, Panoply, etc.).

Attributes
----------

Storing the attributes of the data in its metadata
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


HDF5 file format allows the storage of attributes in the metadata of the groups and datasets. We therefore propose to store all the attributes concerning an experiment in the metadata of its parent group:

.. code-block:: bash

    file.h5
    └── Brillouin (group)
        ├── Measure (group) -> attributes of the measure
            └── Measure (dataset)


Being a hierarchical format, we also propose to store attributes hierarchically: all attributes of parent group apply to childre groups (if not redefined in children groups). Storing attributes in large files can therefore be done the following way:

.. code-block:: bash

    file.h5
    └── Brillouin (group) -> attributes shared by Measure 0 and Measure 1
        ├── Measure 0 (group) -> other attributes specific to Measure 0
        │   └── Measure (dataset)
        ├── Measure 1 (group) -> other attributes specific to Measure 1
            └── Measure (dataset)

Note that the access to the whole list of attributes applying to a group or dataset will be possible with the HDF5\_BLS package (see *Wrapper.get\_attributes*).

Types of attributes
^^^^^^^^^^^^^^^^^^^

In an effort to avoid any incompatibility, we propose to store the values of the attributes as ascii-encoded text. The library will then convert the strings to the appropriate type (e.g. float, int, etc.).

Organization of the attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Prefix
""""""

We differentiate 5 types of attributes, that we differentiate using the following prefixes:

* SPECTROMETER - Attributes that are specific to the spectrometer used, such as the wavelength of the laser, the type of laser, the type of detector, etc. These attributes are recognized by the capital letter word "SPECTROMETER" in the name of the attribute.
* MEASURE - Attributes that are specific to the sample, such as the date of the measure, the name of the sample, etc. These attributes are recognized by the capital letter word "MEASURE" in the name of the attribute.
* FILEPROP - Attributes that are specific to the original file format, such as the name of the file, the date of the file, the version of the file, the precision used on the storage of the data, etc. These attributes are recognized by the capital letter word "FILEPROP" in the name of the attribute.
* PROCESS - Attributes that are specific to the storage of algorithms. These attributes are recognized by the capital letter word "PROCESS" in the name of the attribute.
* Attributes that are used inside the HDF5 file, such as the "Brillouin\_type" attribute. These attributes are the only ones without a prefix.

Units
"""""

The name of the attributes contains the unit of the attribute if it has units, in the shape of an underscore followed by the unit in parenthesis. Some parameters will also be given following a given norm, such as the ISO8601 for dates. These norms are not specified in the name of the attribute. Here are some examples of attributes:

* "SPECTROMETER.Detector\_Type" is the type of the detector used.
* "MEASURE.Sample" is the name of the sample.
* "MEASURE.Exposure\_(s)" is the exposure of the sample given in seconds
* "MEASURE.Date\_of\_measurement" is the date of the measurement, stored following the ISO8601 norm.
* "FILEPROP.Name" is the name of the file.

Unification and Versioning of attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To unify the name of attributes between laboratories, we propose to use a spreadsheet that contains the list of attributes, their definition, their unit and an example of value. This spreadsheet is available on the project repository and is updated as new attributes are added to the project. Each attribute has a version number that is also stored in the attributes of each data attribute (under FILEPROP.version).

This spreadsheet will also be the preferred way to define attributes for the measures and the HDF5\_BLS package allows to read and import the attributes directly from this spreadsheet (see *Wrapper.import\_properties\_data*).

Storing analysis and treatment processes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Analysis and treatment processes are stored in the "PROCESS" attribute of the treatment groups. This attribute is a JSON file converted to a string, which contains the list of treatment steps performed on the data. This JSON file has the following structure:

.. code-block:: bash

    {
        "name": "The name of the algorithm",
        "version": "v 0.1",
        "author": "Author name and affiliation",
        "description": "The description of the algorithm",
        "functions": [
        {
            "function": "The 1st function name in the class",
            "parameters": {
                "parameter_1": value,
                "parameter_2": value,
                ...
            },
            "description": "The description of the function"
        },
        {
            "function": "The 2nd function name in the class",
            "parameters": {
                "parameter_1": value,
                "parameter_2": value,
                ...
            },
            "description": "The description of the function"
        },
        ...
        ]
    }

When the treatment is performed using the modules of the HDF5\_BLS package, this attribute is automatically updated. Note that custom treatments can also be stored in this attribute by the user.

This attribute can be exported to a standalone JSON file using the library. This attribute also allows the library to re-apply the treatment to the data, and modify steps of the treatment if needed.  
