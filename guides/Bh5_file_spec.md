# Proposal for version 0.1 of the .Bh5 file format

## General features:
- The specification defines the minimum set of groups/datasets/attributes that must be implemented. More can be added while still complying with the specs
- The exact name of the fields defined by the specification need to be used (case sensitive)
- Compression and filters to individual datasets can be added since they are handled transparently by the HDF5 library; see [documentation](https://docs.hdfgroup.org/archive/support/HDF5/faq/compression.html)
- Strings must be stored as UTF-8
- Datetimes must be represented as a string in [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html) format
- For names of datasets/attributes that include units the convention is to add them after the last '_' (**To discuss:** what is the best way to store them so that they can be retrieved in an automatic and unambiguos way?); avoid using symbols that are special characters in popular langueges (e.g. '(', '=', '+', etc.)
- Enums start from 0

## Structure:
|   /

|   /Brillouin\_data

|   ---- /Metadata

|   ---- ---- /Experimental\_parameters

|   ---- ---- /Spectrometer

|   ---- ---- ---- /IRF [1D float] (optional)

|   ---- /Data{n}

|   ---- ---- /Raw\_data (optional)

|   ---- ---- /PSD

|   ---- ---- /Frequency

|   ---- ---- /Spatial\_position\_um [1D compound]

|   ---- ---- /Parameters (optional)

|   ---- ---- /Image (optional)

|   ---- ---- ---- /Index [3D int]

|   ---- ---- /Calibration\_index [1D int] (optional)

|   ---- ---- /Timestamp\_ms [1D float] (optional)

|   ---- ---- /Analysis{m}

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
  - **‘Version’ [String]**: version of the specification that the current file is complying with (e.g. ‘0.1’); the numbering should follow the conventions of [semantic versioning](https://semver.org/)
  - **‘SubTypeID’ [uint32]**: identifier of the specific subtype .Bh5 file that is being used. ID 0x00000000 to 0x7FFFFFFF have to be agreed upon and defined on the specifications, while 0x80000000 to 0xFFFFFFFF are free to use as custom subtypes; default is 0
- **‘/Metadata’** (group): 
  - **‘Experimental\_parameters’** (group) has the attributes reported in the excel spreadsheet; we should make a protected datasheet, so users can only input the parameters and not change the structure and have a description there for the meaning and the type of each parameter.
  - **‘Spectrometer’** (group) same as ‘Experimental\_parameters’. It might also contain:
    - **IRF [float]** (optional): a 1D array containing the impulse response function of the spectrometer. It must have an attribute ‘Frequency\_GHz’ [float], of the same length, containing the frequency axis. 
- **‘/data{n}’** (group) containing the data of the current timepoint; it doesn’t need to be necessarily a timepoint in a timelapse, it could also be a measurement at different temperature or whatever fits under the concept of subsequent measurements. It can have any of the attributes defined in ‘Experiment\_parameters’ (if different); specifically, defining the ‘Datetime’ attribute is recommended. If the .Bh5 contains only a single timepoint, this group must still be defined and called ‘data0’. Additionally it might have the following attributes:
  - **‘Parameters_name’ [string]** (optional): contains as many elements as parameters that are varied experimentally. The name should contain the units as well; for example, if concentration and temperature are varied, Parameters_name=['concentration_nM', 'temperature_C']
  - **‘Parameters’ [string]** (optional): the values for the parameters used to acquired the data contained in this specific '/data{n}' group
- **‘/data{n}/Raw_data’** (optional group): the actual content depends on the technique; it might be better defined for a specific ‘SubTypeID'
- **‘/data{n}/PSD’ [float]**: 2D (or more) dataset where the first dimension corresponds to the number of spatial positions in the sample and the second dimension contains the spectral information. Optionally can have more dimensions, when for each voxel in the sample multiple spectra are acquired (e.g. angle resolved measurements); the new dimensions must be inserted in-between (i.e. the “voxels” and spectral dimensions must always be the first and the last, to make the broadcast of the ‘Frequency’ dataset easier) 
- **‘/data{n}/Frequency’ [float]**: it must have the same size as ‘PSD’ or fewer dimensions; in the latter case it will be broadcasted to the size of ‘Amplitude’ (starting from the right), similarly to [Numpy broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html); e.g. if ‘Frequency’ is 1D  and ‘Amplitude’ is 2D, ‘Frequency’ must have the same length as the second dimension of ‘Amplitude’ (in this case the result of broadcasting is assuming that the frequency axis is the same for all the spatial positions). 
  It must have the attribute:
    - **‘Unit’ [string]**: specifying the unit (e.g. ‘GHz’, ‘px’) as a string; the possibility of having ‘px’ (or different unit) as a unit allows to accommodate cases when the calibration doesn’t provide absolute frequency (e.g. relative to the calibration material)
- **‘/data{n}/Spatial\_position\_um’ [compound {x:float, y:float, z:float}]**: 1D dataset containing the x,y,z coordinates in um on the sample
- **‘/data{n}/Parameters’ [float]** (optional): in case ‘Amplitude’ has more than 2 dimensions (let’s call the number of dimensions of ‘Amplitude’ n\_Amp), ‘Parameters’ must have n\_Amp-2 dimensions and contain the parameters at which the spectra were acquired (e.g. for an angle-resolved measurement the angle at which the spectrum was acquired). It must also have the following attributes:
    - **‘Name’ [string]**: a 1D array with size n\_Amp-2 containing the names of the parameters including the unit (e.g. ‘Angle_deg’)
- **‘/data{n}/Image’** (optional group) containing the association between the position in a 3D grid and the data in the ‘Analysed\_data’ group; the order of dimensions is ZYX; the image must always have 3 dimensions, where the unused dimensions can be set to 1:
  - **‘Index’ [int]**: used to assign a specific pixel to the corresponding PSD; if the scanning is done in non-cartesian coordinates -1 can be included to fill the "empty" pixels
  
  It also contains the following attributes:
    - **‘element_size_um’ [float]**: array with 3 elements containing the pixel size (in um) for z, y, x 
  
  N.B. in principle, the 3D grid could be reconstructed from the dataset 'Spatial_position_um', but it is good to have the assignments of pixels to 3D coordinates stored in this group to avoid computing it every time and also to allow for different way for reconstructing the image (in case it is useful) 
- **‘/data{n}/Calibration\_index’ [int]** (optional)**:** zero-based index (the idea being that, if multiple calibration spectra are acquired while imaging, we need to know which calibration data is used for the current spectrum)
- **‘/data{n}/Timestamp\_ms’ [float]** (optional): milliseconds from the beginning of the experiment, as defined in the ‘datetime’ attribute of the current ‘data{n}’ group (if defined, or arbritary otherwise) when the current spectrum was acquired
  
- **‘/data{n}/Analysis{m}’** (group) contains the results of the analysis on the spectral data; the index 'm' allows for the case of multiple pipelines being performed on the same data (in that case a group for each of them must be created). It contains the following datasets. All datasets must be 1D with the same length. The datasets containing the parameters extracted from the spectra (i.e. Shift\_{i}\_GHz, etc.) can have more dimensions, in order to match the dimensions in the PSD dataset. Note that the word ‘dataset’ here is used in the way that it is defined by HDF5, not in an experimental sense; the way one should think about the PSD dataset and the datasets in 'Analysis{m}' is like a table containing a list of voxels acquired in the sample with their corresponding Brillouin shift, width, etc.
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
  
- **‘/data{n}/Calibration’** (optional group) it contains the following datasets (N.B. if the m-th calibration data is the same as a previous timepoint, one can just use the attribute ‘same\_as’ without repeating the data; **look into the option of using soft links**):
  - **‘{m}’ [float]**: a 1D dataset containing the m-th calibration spectrum (where m is referring to ‘/Calibration\_index’); in case there are multiple calibration materials (or reference frequency, e.g. in case of EOMs) the name of the dataset must be ‘m:j’, where j=0,… correspond to one material (frequency); it can optionally have an attribute **‘Timestamp\_ms’ [float]** corresponding to the milliseconds elapsed from ‘/data{n}/Calibration/Datetime’

  It also contains the following attributes:
  - **‘same\_as’ [string]** (optional): to be used when the calibration data is the same as another ‘data{n}’; it contains the name of the group (e.g. ‘/data0’)
  - **‘Description’ [string]** (optional): it describes how the calibration is performed
  - **‘Temperature\_C’ [float]** (optional): the temperature of the calibration material (if relevant)
  - **‘Datatime’ [string]** (optional): a [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html) representation of the time when the (first) calibration spectrum was acquired
  - **‘Shift\_m\_GHz’ [string]** (optional): Brillouin shift of the m-th calibration material (or frequency); the name must be ‘Shift\_0\_GHz’ in case a single material is used.
  - **‘FSR\_GHz’ [float]** (optional): The free spectral range of the spectrometer (in case it is a parameter that is used for calibration)
