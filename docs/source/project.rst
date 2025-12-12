Project development
===================

Project specification sheet
---------------------------

The project is based on the following specifications:


.. role:: grayheavy
.. role:: graylight
.. role:: graysuperlight
.. role:: italic

:grayheavy:`1. Format`

:graylight:`1.1. Simplicity`

:graysuperlight:`1.1.1. The format should be conceptually simple, unambiguous and easy to create and use.`

   - :italic:`1.1.1.1. Storing a single measure should be easy and unambiguous.`
   - :italic:`1.1.1.2. Storing arguments associated with a measure should be easy and unambiguous. The arguments should have a predefined nomenclature.`
   - :italic:`1.1.1.3. Storing measures performed with changes of different hyper parameters should be easy and unambiguous.`
   - :italic:`1.1.1.4. Storing a PSD and Frequency arrays extracted from a measure should be easy and unambiguous.`
   - :italic:`1.1.1.5. Storing the result of a treatment should be easy and unambiguous.`
   - 
:graylight:`1.2. Universality`

:graysuperlight:`1.2.1. The format should be compatible with existing HDF5 softwares.`

   - :italic:`1.2.1.1. Opening the file with an HDF5 viewer should give us access to a user-friendly hierarchical structure.`

:graysuperlight:`1.2.2. The format should allow the storage of complemetary datasets obtained with other modalities (e.g. Raman, NMR, fluorescence, etc.).` 

   - :italic:`1.2.2.1. The format should make a clear distinction between datasets related to BLS measurements and other datasets.`
   - :italic:`1.2.2.2. The format should allow user to store datasets related to other modalities with an arbitrary structure in the first description of the format.`

:graysuperlight:`1.2.3. The format should be adapted for storing Brillouin spectra obtained with different techniques.`

   - :italic:`1.2.3.1. The format should allow measures obtained with all techniques to be stored. This includes the sotrage of datasets with arbitrary dimensions, additional technique-specific datasets and additional technique-specific attributes.`

:graylight:`1.3. Expandability`

:graysuperlight:`1.3.1. The format should accomodate future needs`

   - :italic:`1.3.1.1. The format should classify the data preferably by the hyper parameters that were varied for the experiment.`

:grayheavy:`2. Analysis and treatment`

:graylight:`2.1. Power Spectral Density`

:graysuperlight:`2.1.1. It must be possible to obtain a Power Spectral Density.`

   - :italic:`2.1.1.1. All relevant information and datasets for the obtention of the PSD should be in the same file at the moment of treatment.`
   - :italic:`2.1.1.2. All relevant information and datasets should be unambiguously and simply accessible.`
   - :italic:`2.1.1.3. The PSD and Frequency arrays should be stored unambiguously in the file so that we know which arrays and parameters were used to obtain them.`
   - :italic:`2.1.1.4. The process of obtaining the PSD should be documented in the file in a reusable way.`

:graysuperlight:`2.1.2. It must be possible to create custom algorithms to extract the PSD and frequency.`

   - :italic:`2.1.2.1. The function(s) extracting the PSD and frequency should have a fixed nomenclature for their name.`
   - :italic:`2.1.2.2. The function(s) extracting the PSD and frequency should all return the same type of data.`
   - :italic:`2.1.2.3. The function(s) extracting the PSD and frequency should all use the same type of documentation.`
   - :italic:`2.1.2.4. All function(s) extracting the PSD and frequency should be stored in the same module.`
   - :italic:`2.1.2.5. All function(s) extracting the PSD and frequency should also return the parameters they used to obtain the PSD and frequency, with which it is possible to reproduce the PSD and frequency.`

:graylight:`2.2. Extraction of peak information`

:graysuperlight:`2.2.1. The PSD and Frequency datasets should allow for a unified way of extracting information, independent on the spectrometer used.`

   - :italic:`2.2.1.1. It should be unambiguous to assign a frequency axis to a PSD dataset based on the PSD and Frequency arrays.`

:graysuperlight:`2.2.2. The format should allow the user to extract information with different treatment and store all the results in the same file.`

   - :italic:`2.2.2.1. The treatments should have an identifier that can be incremented to allow the user to store different treatments.`
   - :italic:`2.2.2.2. Each new treatment should also store the parameters used to obtain the information in a way that the user can reproduce the information.`

:grayheavy:`3. Graphical User Interface`

:graylight:`3.1. Simplicity`

:graysuperlight:`3.1.1. Interaction with files and attributes should be as intuitive as possible.`

   - :italic:`3.1.1.1. Adding a file (attribute file or data file) to the format should be possible by dragging and dropping it in the GUI.`
   - :italic:`3.1.1.2. Changing a visible property of a dataset or group should be possible by left clicking on it and editing its value in the GUI.`
   - :italic:`3.1.1.3. A right click on a file or group should open a context menu with the action options to perform on the file or group.`
   - :italic:`3.1.1.4. It should be possible to perform the same action in the GUI by at least 2 redundant ways.`
   - :italic:`3.1.1.5. The GUI should be idiot proof and be able to flag all actions that might damage the file, make a treatment impossible, or induce any type of incompatibility.`

Project structure
-----------------

The project is structured around two axes:

- **File format**: Design a HDF5-based file format that is minimally constrained and that allows all BLS-derived data to be stored
- **Data processing**: Create data processing tools to treat BLS measures and extract relevant parameters from them
  - **For unifying the obtention of Power Spectral Density (PSD)**: Create a unified way to obtain the PSD from a measure given a spectrometer, and to store the results of the treatment of the data
  - **For extracting information from the PSD**: Create a unified way to extract information from the PSD, such as the shift, the linewidth, the amplitude, the BLT, etc.

Project timeline
----------------

The timeline of the project is divided in four phases:

- **Phase 1**: Design a HDF5-based file format that is minimally constrained and that allows all BLS-derived data to be stored
- **Phase 2**: Stress test the file format to make sure it answers all the needs of the community, in particular ensure compatibility with different spectrometers
- **Phase 3**: Create data processing tools to treat BLS measures and extract relevant parameters from them
- **Phase 3**: Define normalization rules to store particular data formats (single spectra, series of spectra evolving with respect to one hyper parameter, spatial images, etc.), and develop dedicated visualization tools to display the data, metadata and results.

User interfaces
---------------

The project consists of 3 independent Python packages to be used in Python scripts or Jupyter notebooks:

- **HDF5_BLS**: The package to create and manipulate HDF5 files
- **HDF5_BLS_analyse**: The package to perform the conversion of BLS measures to an associated Power Spectral Density (PSD)
- **HDF5_BLS_treat**: The package to process the PSD to extract relevant information from it

To allow a use of the project without recurring to scripts, a Graphical User Interface (GUI) called *HDF5_BLS - The GUI* is accessible.
The GUI is now capable of:

- Creating HDF5 files following the structure of HDF5_BLS v1.0:
 
    - Structure the file in a hierarchical way
    - Import measure data (drag and drop functionality implemented)
    - Import attributes from a CSV or Excel spreadsheet file (drag and drop functionality implemented)
    - Modify parameters of data both by group and individually from the GUI
  
- Inspect existing HDF5 files and in particular, ones made with the HDF5_BLS package
- Export sub-HDF5 files from meta files
- Export Python or Matlab code to access individual datasets
- Visualize 2D arrays as images
- Analyse raw spectra obtained with a VIPA spectrometer