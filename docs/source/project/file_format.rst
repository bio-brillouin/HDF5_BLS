The file organization
=====================

A single measure
----------------

This project aims at defining a standard for storing Brillouin Light Scattering measures and associated treatment in a HDF5 file.

HDF5 stands for "Hierarchical Data Format" and is a file format that allows the storage of data in a hierarchical structure. This structure allows to store data in a way that is both human and machine readable. The structure of the file is based on the following base structure, which corresponds to the structure of a file containing a single measure (*Measure*) where no parameters have been stored:

.. treeview::

    - :dir:`file` file.h5
        - :dir:`folder` Brillouin (group)
            - :dir:`folder` Measure (group)
                - :dir:`file` Measure (dataset)

The dimensionality of the dataset is free, there are therefore by design virtually no restrictions on the data that can be stored in this format.

The organization of the file is based on the following principles:

* The file is organized in groups and datasets, which allows to store data in a hierarchical structure.
* Only one dataset corresponding to a BLS measure can be stored per group.
* The groups are used to organize the file and store metadata and parameters related to the measure, and the datasets are used to store the actual data.

A single measure with physical meaning
--------------------------------------

From the single measure file, we need to move towards a structure where datasets have a meaning and are not just a collection of numbers. To do so, we propose to always refer to the Power Spectral Density (PSD) as the basis for a measure. In this spirit, we add to our measure group two datasets containing the PSD and the corresponding frequency axis:


.. treeview::

    - :dir:`file` file.h5
        - :dir:`folder` Brillouin (group)
            - :dir:`folder` Measure (group)
                - :dir:`file` Measure (dataset)
                - :dir:`file` PSD (dataset)
                - :dir:`file` Frequency (dataset)

To not constrain the names of the datasets, we assign to each of these datasets, a "Brillouin\_type" attribute. This attribute is a string that allows to know the type of the element:

.. treeview::

    - :dir:`file` file.h5
        - :dir:`folder` Brillouin (group)
            - :dir:`folder` Measure (group)
                - :dir:`file` Measure (dataset)
                    - :icon:`icon_attr` Brillouin_type: "Raw_data"
                - :dir:`file` PSD (dataset)
                    - :icon:`icon_attr` Brillouin_type: "PSD"
                - :dir:`file` Frequency (dataset)
                    - :icon:`icon_attr` Brillouin_type: "Frequency"

Multiple measures stored in the same file
-----------------------------------------

In the case where we want to store multiple measures in the same file, we can multiply the number of groups stored under the "Brillouin" group.  For the same reason than before, to not constrain the names of the group, we'll assign them "Brillouin\_type" attributes to differentiate the groups that store groups ("Root") from the groups that store measures ("Measure"):

.. treeview::

    - :dir:`file` file.h5
        - :dir:`folder` Brillouin (group)
            - :dir:`folder` RWPE1 organoids (group)
                    - :icon:`icon_attr` Brillouin_type: "Root"
                - :dir:`folder` Morphogenesis day 1 (group)
                        - :icon:`icon_attr` Brillouin_type: "Root"
                    - :dir:`folder` Sample 1 (group)
                            - :icon:`icon_attr` Brillouin_type: "Measure"
                        - :dir:`file` Measure (dataset)
                            - :icon:`icon_attr` Brillouin_type: "Raw_data"
                        - :dir:`file` PSD (dataset)
                            - :icon:`icon_attr` Brillouin_type: "PSD"
                        - :dir:`file` Frequency (dataset)
                            - :icon:`icon_attr` Brillouin_type: "Frequency"
                    - :dir:`folder` Sample 2 (group)
                            - :icon:`icon_attr` Brillouin_type: "Measure"
                        - :dir:`file` Measure (dataset)
                            - :icon:`icon_attr` Brillouin_type: "Raw_data"
                        - :dir:`file` PSD (dataset)
                            - :icon:`icon_attr` Brillouin_type: "PSD"
                        - :dir:`file` Frequency (dataset)
                            - :icon:`icon_attr` Brillouin_type: "Frequency"
                    - :dir:`folder` ...
                - :dir:`folder` Morphogenesis day 1 (group)
                        - :icon:`icon_attr` Brillouin_type: "Root"
                    - :dir:`folder` ...
            - :dir:`folder` H6C7 organoids (group)
                    - :icon:`icon_attr` Brillouin_type: "Root"
                - :dir:`folder` ...
            - :dir:`folder` ...

Multiple measures stored with their results
-------------------------------------------

The next step is to store the results of the treatment of the measure. The difficulty lies in the fact that multiple treatments can be applied to the same measure. To solve this problem, we propose to store all the results of a treatment in a dedicated "Treatment" group. This group will be named after the treatment and will contain for example the shift, the linewidth, the amplitude, the BLT, the error on the shift, etc. 

Following the same logic, each of these datasets will be associated to a "Brillouin\_type" attribute to recognize the nature of the dataset:

.. treeview::

    - :dir:`file` file.h5
        - :dir:`folder` Brillouin (group)
            - :dir:`folder` RWPE1 organoids (group)
                    - :icon:`icon_attr` Brillouin_type: "Root"
                - :dir:`folder` Morphogenesis day 1 (group)
                        - :icon:`icon_attr` Brillouin_type: "Root"
                    - :dir:`folder` Sample 1 (group)
                            - :icon:`icon_attr` Brillouin_type: "Measure"
                        - :dir:`file` Measure (dataset)
                            - :icon:`icon_attr` Brillouin_type: "Raw_data"
                        - :dir:`file` PSD (dataset)
                            - :icon:`icon_attr` Brillouin_type: "PSD"
                        - :dir:`file` Frequency (dataset)
                            - :icon:`icon_attr` Brillouin_type: "Frequency"
                        - :dir:`folder` Treatment (group)
                                - :icon:`icon_attr` Brillouin_type: "Frequency"
                            - :dir:`file` Shift (dataset)
                                - :icon:`icon_attr` Brillouin_type: "Shift"
                            - :dir:`file` Linewidth (dataset)
                                - :icon:`icon_attr` Brillouin_type: "Linewidth"
                    - :dir:`folder` Sample 2 (group)
                            - :icon:`icon_attr` Brillouin_type: "Measure"
                        - :dir:`file` Measure (dataset)
                            - :icon:`icon_attr` Brillouin_type: "Raw_data"
                        - :dir:`file` PSD (dataset)
                            - :icon:`icon_attr` Brillouin_type: "PSD"
                        - :dir:`file` Frequency (dataset)
                            - :icon:`icon_attr` Brillouin_type: "Frequency"
                        - :dir:`folder` Treatment (group)
                                - :icon:`icon_attr` Brillouin_type: "Frequency"
                            - :dir:`file` Shift (dataset)
                                - :icon:`icon_attr` Brillouin_type: "Shift"
                            - :dir:`file` Linewidth (dataset)
                                - :icon:`icon_attr` Brillouin_type: "Linewidth"
 
Multiple measures stored with their results and algorithms
----------------------------------------------------------

The file structure is capable of storing not only datasets, attributes related to how the data was collected, in a hierarchical way, but it also allows users to store their scripts. This is particularly useful when the user performs a new kind of data processing, or when he uses the data to generate figures. Any script can be stored in the file as text. Note that in order to differentiate between scripts and "normal" attributes, we recommend using the prefix "script\_" for the attribute name, so as to clearly distinguish them from the other attributes.

These scripts can be in any programming language, and will in the future be runnable from the library itself (particularly to re-generate the figures). Here is an example of how a file storing a script would look like:

.. treeview::

    - :dir:`file` file.h5
        - :dir:`folder` Brillouin (group)
                - :icon:`icon_attr` script_plot_distribution: "import matplotlib.pyplot as plt ..."
                - :icon:`icon_attr` script_plot_treatement: "from scipy.optimize import curve_fit ..."
            - :dir:`folder` RWPE1 organoids (group)
                    - :icon:`icon_attr` Brillouin_type: "Root"
                - :dir:`folder` Morphogenesis day 1 (group)
                        - :icon:`icon_attr` Brillouin_type: "Root"
                    - :dir:`folder` Sample 1 (group)
                            - :icon:`icon_attr` Brillouin_type: "Measure"
                        - :dir:`file` Measure (dataset)
                            - :icon:`icon_attr` Brillouin_type: "Raw_data"
                        - :dir:`file` PSD (dataset)
                            - :icon:`icon_attr` Brillouin_type: "PSD"
                        - :dir:`file` Frequency (dataset)
                            - :icon:`icon_attr` Brillouin_type: "Frequency"
                        - :dir:`folder` Treatment (group)
                                - :icon:`icon_attr` Brillouin_type: "Frequency"
                            - :dir:`file` Shift (dataset)
                                - :icon:`icon_attr` Brillouin_type: "Shift"
                            - :dir:`file` Linewidth (dataset)
                                - :icon:`icon_attr` Brillouin_type: "Linewidth"

.. note::
    
   Scripts are stored as text. There is therefore no limitation on what could be stored as a script. This means the storage solution is compatible with all programming languages, with the limitation of the access to the library and dependencies used in the script.
