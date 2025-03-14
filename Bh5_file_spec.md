# Proposal for version 0.1 of the .Bh5 file format

## General description:
The .Bh5 file format is designed to store Brillouin spectral data along with the results of its analysis.
While it supports the storage of individual spectra acquired under different conditions, its primary focus is on Brillouin microscopy images.
Brillouin microscopy is a hyperspectral imaging technique, where each pixel in the final 3D image corresponds to a full spectrum. 
Individual spectra are arranged in a flattened structure within the '/data_{n}/PSD' dataset.
In this format, the first dimension represents the spatial position, while the second dimension contains the spectral information.
The reconstruction of a 3D image from these spectra is done through the '/data_{n}/Scanning/Cartesian_visualization' dataset, which maps each spatial position onto a 3D grid.
Additionally, the '/data_{n}' groups enable the storage of multiple acquisitions, referred to as time points.
These time points are not limited to conventional time-lapse imaging but can also represent variations in experimental conditions, such as temperature, osmolarity, or other environmental factors.

## General features:
- The specification defines the minimum set of groups/datasets/attributes that must be implemented. More can be added while still complying with the specs
- The exact name of the fields defined by the specification need to be used (case sensitive)
- Avoid using symbols that are special characters in popular languages (e.g. '(', '=', '+', etc.) in names of datasets/attributes
- Compression and filters to individual datasets can be added since they are handled transparently by the HDF5 library; see [documentation](https://docs.hdfgroup.org/archive/support/HDF5/faq/compression.html)
- Strings must be stored as UTF-8
- Datetimes must be represented as a string in [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html) format
- For datasets that need units add an attribute named 'units' that contains the name of the units as a string; if an attribute (e.g. named 'attribute_x') needs units, add another attribute called 'attribute_x_units' at the same hierarchical level and store the name of the unit as a string
- Enums should be stored as string (but preferably the library used to generate the Bh5 should still expose enums to the user, to avoids typos in the name of the elements)

## Structure:
|   /

|   /Brillouin\_data

|   ---- /Metadata

|   ---- ---- /Experimental\_parameters

|   ---- ---- /Spectrometer

|   ---- ---- ---- /IRF [1D float] (optional)

|   ---- /Data_{n}

|   ---- ---- /Raw\_data (optional)

|   ---- ---- /PSD

|   ---- ---- /Frequency

|   ---- ---- /Scanning

|   ---- ---- ---- /Spatial\_map [1D compound] (optional)

|   ---- ---- ---- /Cartesian\_visualization [3D int]

|   ---- ---- /Parameters (optional)

|   ---- ---- /Calibration\_index [1D int] (optional)

|   ---- ---- /Timestamp\_ms [1D float] (optional)

|   ---- ---- /Analysis_{m}

|   ---- ---- ---- /Shift\_{i}\_GHz [1D (or more) float]

|   ---- ---- ---- /Width\_{i}\_GHz [1D (or more) float]

|   ---- ---- ---- /Amplitude\_{i} [1D (or more) float]

|   ---- ---- ---- /Fit\_error\_{i} (optional)

|   ---- ---- ---- ---- /R2 [1D (or more) float]

|   ---- ---- ---- ---- /RMSE [1D (or more) float]

|   ---- ---- ---- ---- /Cov_matrix [1D (or more) compound]

|   ---- ---- /Calibration (optional)

|   ---- ---- ---- /{i} [1D (or more) float]

## Detailed description of the content of the file:
- **‘/’** (root group) must have the following attributes:
  - **‘Bh5_version’ [String]**: version of the specification that the current file is complying with (e.g. ‘0.1’); the numbering should follow the conventions of [semantic versioning](https://semver.org/)
  - **‘SubTypeID’ [uint32]**: identifier of the specific subtype .Bh5 file that is being used. ID 0x00000000 to 0x7FFFFFFF have to be agreed upon and defined on the specifications, while 0x80000000 to 0xFFFFFFFF are free to use as custom subtypes; default is 0
  - **‘Authors’ [String]** (optional): information about the authors of the file (e.g. name, contact, etc...)
  - **‘Lab’ [String]** (optional): information about lab and/or institute where the data was generated
  
All the following groups are inside the ‘/Brillouin\_data’ group:
- **‘/Metadata’** (group): 
  - **‘Experimental\_parameters’** (group) has the attributes reported in the excel spreadsheet; we should make a protected datasheet, so users can only input the parameters and not change the structure and have a description there for the meaning and the type of each parameter.
  - **‘Spectrometer’** (group) attributes defined in the same excel sheet as ‘Experimental\_parameters’. It might also contain:
    - **IRF [float]** (optional): a 1D array containing the impulse response function of the spectrometer. It must have an attribute ‘Frequency’ [float] (with the corresponding ‘Frequency_units’ [string]) of the same length, containing the frequency axis. 
- **‘/data_{n}’** (group) containing the data of the current timepoint; it doesn’t need to be necessarily a timepoint in a timelapse, it could also be a measurement at different temperature or whatever fits under the concept of subsequent measurements. It can have any of the attributes defined in ‘Experiment\_parameters’ (if different); specifically, defining the ‘Datetime’ attribute is recommended. If the .Bh5 contains only a single timepoint, this group must still be defined and called ‘data_0’. Additionally it might have the following attributes:
  - **‘Parameters_name’ [string]** (optional): contains as many elements as parameters that are varied experimentally. If used ‘Parameters_name_units’ should be also defined
  - **‘Parameters’ [string]** (optional): the values for the parameters used to acquired the data contained in this specific '/data_{n}' group
- **‘/data_{n}/Raw_data’** (optional group): the actual content depends on the technique; it might be better defined for a specific ‘SubTypeID'
- **‘/data_{n}/PSD’ [float]**: 2D (or more) dataset where the first dimension corresponds to the number of spatial positions in the sample and the second dimension contains the spectral information. Optionally can have more dimensions, when for each voxel in the sample multiple spectra are acquired (e.g. angle resolved measurements); the new dimensions must be inserted in-between (i.e. the “voxels” and spectral dimensions must always be the first and the last, to make the broadcast of the ‘Frequency’ dataset easier) 
- **‘/data_{n}/Frequency’ [float]**: it must have the same size as ‘PSD’ or fewer dimensions; in the latter case it will be broadcasted to the size of ‘PSD’ (starting from the right), similarly to [Numpy broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html); e.g. if ‘Frequency’ is 1D  and ‘PSD’ is 2D, ‘Frequency’ must have the same length as the second dimension of ‘PSD’ (in this case the result of broadcasting is assuming that the frequency axis is the same for all the spatial positions). 
  It must have the attribute:
    - **‘units’ [string]**: specifying the units (e.g. ‘GHz’, ‘px’) as a string; the possibility of having ‘px’ (or different unit) as a unit allows to accommodate cases when the calibration doesn’t provide absolute frequency (e.g. relative to the calibration material)
- **‘/data_{n}/Scanning/Spatial\_map’ [compound {x:float, y:float, z:float}]** (optional): 1D dataset containing the x,y,z coordinates on the sample; if ‘Cartesian\_visualization’ is defined, ‘Spatial\_map’ can be omitted
- **‘/data_{n}/Scanning/Cartesian\_visualization’ [3D int]** contains an index which associates the position in the 3D grid to the first dimension in ‘PSD’ (thus obviously the index needs to be smaller than the number of elements in ‘PSD’). The order of dimensions is ZYX and the 3 dimensions must always be present, where the unused dimensions can be set to 1. If the scanning is done in non-cartesian coordinates -1 can be included to fill the "empty" pixels

  It must also contains the following attributes:
    - **‘element_size’ [float]**: array with 3 elements containing the pixel size for z, y, x 
    - **‘element_size_units’ [string]**: array with 3 elements containing the units for the element_size (e.g. 'um') 
  
  N.B. in principle, the 3D grid could be reconstructed from the dataset '/Scanning/Spatial\_map' (if present), but it is good to have it always defined to avoid computing the assignments of spectra to 3D coordinates every time and also to allow for different way for reconstructing the image (in case it is useful) 
- **‘/data_{n}/Parameters’ [float]** (optional): in case ‘PSD’ has more than 2 dimensions (let’s call the number of dimensions of ‘PSD’ n\_PSD), ‘Parameters’ must have n\_PSD-2 dimensions and contain the parameters at which the spectra were acquired (e.g. for an angle-resolved measurement the angle at which the spectrum was acquired). It must also have the following attributes:
    - **‘Name’ [string]**: a 1D array with size n\_PSD-2 containing the names of the parameters including the unit (e.g. ‘Angle_deg’)
- **‘/data_{n}/Calibration\_index’ [int]** (optional)**:** zero-based index (the idea being that, if multiple calibration spectra are acquired while imaging, we need to know which calibration data is used for the current spectrum)
- **‘/data_{n}/Timestamp\_ms’ [float]** (optional): milliseconds from the beginning of the experiment, as defined in the ‘datetime’ attribute of the current ‘data_{n}’ group (if defined, or arbritary otherwise) when the current spectrum was acquired
  - **‘/data_{n}/Analysis_{m}’** (group) contains the results of the analysis on the spectral data; the index 'm' allows for the case of multiple pipelines being performed on the same data (in that case a group for each of them must be created). It contains the following datasets. All datasets must be 1D with the same length. The datasets containing the parameters extracted from the spectra (i.e. Shift\_{i}\_GHz, etc.) can have more dimensions, in order to match the dimensions in the PSD dataset. Note that the word ‘dataset’ here is used in the way that it is defined by HDF5, not in an experimental sense; the way one should think about the PSD dataset and the datasets in 'Analysis{m}' is like a table containing a list of voxels acquired in the sample with their corresponding Brillouin shift, width, etc.
  - **‘Shift\_{i}\_GHz’ [float]**: n=0,… if multiple peaks are fitted
  - **‘Width\_{i}\_GHz’ [float]**: n=0,… if multiple peaks are fitted
  - **‘Amplitude\_{i}’ [float]**: n=0,… if multiple peaks are fitted
  - **‘Fit\_error\_{i}’** (optional group) containing the following datasets:
    - **‘RMSE’ [float]** (optional)
    - **‘R2’ [float]** (optional)
    - **‘Cov_matrix’ [float]** (optional) (we need to discuss the number of dimensions)
  - Additional optional datasets 
  
  It also contains the following attributes:
  - **‘Fit\_model’ [enum:{other, Lorentzian, DHO, Voigt}]**
  - **‘Corrections’ [string]**: text describing any corrections that is applied to the fitted data (e.g. for NA broadening, deconvolution, etc.)
  
- **‘/data_{n}/Calibration’** (optional group) it contains the following datasets; **N.B. if the whole calibration group (or an indivual {m} dataset) is the same as one in another data_{n}, one could create a [link](https://docs.h5py.org/en/stable/high/group.html#link-classes) to that instead of repeating the data; that implies that, when writing to the file, one must be careful if there are multiple links pointing at the same object**:
  - **‘{m}’ [float]**: a 1D dataset containing the m-th calibration spectrum (where m is referring to ‘/Calibration\_index’); in case there are multiple calibration materials (or reference frequency, e.g. in case of EOMs) the name of the dataset must be ‘m:j’, where j=0,… correspond to one material (frequency); it can optionally have an attribute **‘Timestamp\_ms’ [float]** corresponding to the milliseconds elapsed from ‘/data_{n}/Calibration/Datetime’

  It also contains the following attributes:
  - **‘Description’ [string]** (optional): it describes how the calibration is performed
  - **‘Temperature_C’ [float]** (optional): the temperature of the calibration material (if relevant)
  - **‘Datatime’ [string]** (optional): a [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html) representation of the time when the (first) calibration spectrum was acquired
  - **‘Shift\_m\_GHz’ [string]** (optional): Brillouin shift of the m-th calibration material (or frequency); the name must be ‘Shift\_0\_GHz’ in case a single material is used.
  - **‘FSR\_GHz’ [float]** (optional): The free spectral range of the spectrometer (in case it is a parameter that is used for calibration)
