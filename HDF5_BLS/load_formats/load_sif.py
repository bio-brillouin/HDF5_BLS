import os
import sif_parser
from datetime import datetime
from HDF5_BLS.load_formats.errors import LoadError

def load_sif_base(filepath, parameters = None):
    """Loads npy files

    Parameters
    ----------
    filepath : str                           
        The filepath to the npy file
    parameters : dict, optional
        A dictionary with the parameters to load the data, by default None. A list of possible parameters is given in the "Notes" section of this docstring.

    Returns
    -------
    dict
        The dictionary with the data and the attributes of the file stored respectively in the keys "Data" and "Attributes"
    
    Notes
    -----
    Possible parameters are:
    - shape: tuple, optional
        The shape of the data. If not given, the shape is inferred from the file.
    - raster: tuple, optional
        Tuple containing the axises along which the data has to be rearranged to correspond to a raster plot. If not given, the data is not rearranged. Note that the axises are given in the order of the axes in the file, for example (0)
    """
    name, _ = os.path.splitext(filepath)
    attributes = {}

    data, info = sif_parser.np_open(filepath)

    attributes['MEASURE.Exposure_(s)'] = str(info["ExposureTime"])
    attributes['SPECTROMETER.Detector_Model'] = info["DetectorType"]
    attributes['MEASURE.Date_of_measure'] = datetime.fromtimestamp(info["ExperimentTime"]).isoformat()
    attributes['FILEPROP.Name'] = name

    if not parameters is None:
        if "shape" in parameters.keys(): 
            try: data = data.reshape(parameters["shape"])
            except: raise LoadError(f"The shape {parameters['shape']} is not compatible with the data.")
        if "raster" in parameters.keys() and parameters["raster"]: 
            for ax in parameters["raster"]: 
                for i in range(data.shape[ax]):
                    if i % 2 == 1:  # Invert every second line
                        data = data.swapaxes(0, ax)
                        data[i] = data[i, ::-1]
                        data = data.swapaxes(0, ax)
                
    dic = {"Raw_data":{"Name": "Raw data", "Data": data}, 
           "Attributes": attributes}
    return dic