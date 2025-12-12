The file format
===============

A single measure
----------------

This project aims at defining a standard for storing Brillouin Light Scattering measures and associated treatment in a HDF5 file.

HDF5 stands for "Hierarchical Data Format" and is a file format that allows the storage of data in a hierarchical structure. This structure allows to store data in a way that is both human and machine readable. The structure of the file is based on the following base structure, which corresponds to the structure of a file containing a single measure (*Measure*) where no parameters have been stored:

.. code-block:: bash

    file.h5
    └── Brillouin (group)
        └── Measure (group)
            └── Measure (dataset)


The dimensionality of the dataset is free, there are therefore by design virtually no restrictions on the data that can be stored in this format.

The organization of the file is based on the following principles:

* The file is organized in groups and datasets, which allows to store data in a hierarchical structure.
* Only one dataset corresponding to a measure can be stored per group. 
* The groups are used to organize the file and store metadata and parameters related to the measure, and the datasets are used to store the actual data.

A single measure with physical meaning
--------------------------------------

From the single measure file, we need to move towards a structure where datasets have a meaning and are not just a collection of numbers. To do so, we propose to always refer to the Power Spectral Density (PSD) as the basis for a measure. In this spirit, we add to our measure group two datasets containing the PSD and the corresponding frequency axis:

.. code-block:: bash

    file.h5
    └── Brillouin (group)
        └── Measure (group)
            ├── Measure (dataset)
            ├── PSD (dataset)
            └── Frequency (dataset)

To not constrain the names of the datasets, we assign to each of these datasets, a "Brillouin\_type" attribute. This attribute is a string that allows to know the type of the element:

.. code-block:: bash

    file.h5
    └── Brillouin (group)
        └── Measure (group)
            ├── Measure (dataset, Brillouin_type = "Raw data")
            ├── PSD (dataset, Brillouin_type = "PSD")
            └── Frequency (dataset, Brillouin_type = "Frequency")

Multiple measures stored in the same file
-----------------------------------------

In the case where we want to store multiple measures in the same file, we can multiply the number of groups stored under the "Brillouin" group.  For the same reason than before, to not constrain the names of the group, we'll assign them "Brillouin\_type" attributes to differentiate the groups that store groups ("Root") from the groups that store measures ("Measure"):

.. code-block:: bash

    file.h5
    └── Brillouin (group, Brillouin_type = "Root")
        ├── RWPE1 organoids (group, Brillouin_type = "Root")
        │   ├── Morphogenesis day 1 (group, Brillouin_type = "Root")
        │   │   ├── Sample 1 (group, Brillouin_type = "Measure")
        │   │   │   ├── Measure (dataset, Brillouin_type = "Raw data")
        │   │   │   ├── PSD (dataset, Brillouin_type = "PSD")
        │   │   │   └── Frequency (dataset, Brillouin_type = "Frequency")
        │   │   ├── Sample 2 (group, Brillouin_type = "Measure")
        │   │   │   ├── Measure (dataset, Brillouin_type = "Raw data")
        │   │   │   ├── PSD (dataset, Brillouin_type = "PSD")
        │   │   │   └── Frequency (dataset, Brillouin_type = "Frequency")
        │   │   ...
        │   ├── Morphogenesis day 2 (group, Brillouin_type = "Root")
        │   │   ├── ...
        ├── H6C7 organoids (group, Brillouin_type = "Root")
        ├── ...

Multiple measures stored with their results
-------------------------------------------

The next step is to store the results of the treatment of the measure. The difficulty lies in the fact that multiple treatments can be applied to the same measure. To solve this problem, we propose to store all the results of a treatment in a dedicated "Treatment" group. This group will be named after the treatment and will contain for example the shift, the linewidth, the amplitude, the BLT, the error on the shift, etc. 

Following the same logic, each of these datasets will be associated to a "Brillouin\_type" attribute to recognize the nature of the dataset:

.. code-block:: bash

    file.h5
    └── Brillouin (group, Brillouin_type = "Root")
        └── RWPE1 organoids (group, Brillouin_type = "Root")
            └── Morphogenesis day 1 (group, Brillouin_type = "Root")
                ├── Sample 1 (group, Brillouin_type = "Measure")
                │   ├── Measure (dataset, Brillouin_type = "Raw data")
                │   ├── PSD (dataset, Brillouin_type = "PSD")
                │   ├── Frequency (dataset, Brillouin_type = "Frequency")
                │   └── Treatment (group, Brillouin_type = "Treatment")
                │       ├── Shift (dataset, Brillouin_type = "Shift")
                │       ├── Linewidth (dataset, Brillouin_type = "Linewidth")
                └── Sample 2 (group, Brillouin_type = "Measure")
                    ├── Measure (dataset, Brillouin_type = "Raw data")
                    ├── PSD (dataset, Brillouin_type = "PSD")
                    ├── Frequency (dataset, Brillouin_type = "Frequency")
                    └── Treatment (group, Brillouin_type = "Treatment")
                        ├── Shift (dataset, Brillouin_type = "Shift")
                        └── Linewidth (dataset, Brillouin_type = "Linewidth")
 
Multiple measures stored with their results and algorithms
----------------------------------------------------------

The file structure is capable of storing not only datasets, attributes related to how the data was collected, in a hierarchical way, but it also allows users to store their scripts. This is particularly useful when the user performs a new kind of data processing, or when he uses the data to generate figures. Any script can be stored in the file as text. Note that in order to differentiate between scripts and "normal" attributes, we recommend using the prefix "script_" for the attribute name, so as to clearly distinguish them from the other attributes.

These scripts can be in any programming language, and will in the future be runnable from the library itself (particularly to re-generate the figures). Here is an example of how a file storing a script would look like:

.. code-block:: bash

    file.h5
    └── Brillouin (group, Brillouin_type = "Root", script_plot_distributions = "import numpy as np\nimport ...")
        ├── Concentration 1mMol/mL (group, Brillouin_type = "Measure")
        │   ├── PSD (dataset, Brillouin_type = "PSD")
        │   ├── Frequency (dataset, Brillouin_type = "Frequency")
        │   └── Treatment (group, Brillouin_type = "Treatment")
        │       ├── Shift (dataset, Brillouin_type = "Shift")
        │       └── Linewidth (dataset, Brillouin_type = "Linewidth")
        ├── Concentration 2mMol/mL (group, Brillouin_type = "Measure")
        │   ├── PSD (dataset, Brillouin_type = "PSD")
        │   ├── Frequency (dataset, Brillouin_type = "Frequency")
        │   └── Treatment (group, Brillouin_type = "Treatment")
        │       ├── Shift (dataset, Brillouin_type = "Shift")
        │       └── Linewidth (dataset, Brillouin_type = "Linewidth")
        ├── Concentration 3mMol/mL (group, Brillouin_type = "Measure")
        │   ├── ...
