import os
import sif_parser
from datetime import datetime

def load_sif_base(filepath):
    """Loads npy files

    Parameters
    ----------
    filepath : str                           
        The filepath to the npy file
    
    Returns
    -------
    dict
        The dictionnary with the data and the attributes of the file stored respectively in the keys "Data" and "Attributes"
    """
    name, _ = os.path.splitext(filepath)
    attributes = {}

    data, info = sif_parser.np_open(filepath)


    attributes['MEASURE.Exposure_(s)'] = str(info["ExposureTime"])
    attributes['SPECTROMETER.Detector_Model'] = info["DetectorType"]
    attributes['MEASURE.Date_of_measure'] = datetime.fromtimestamp(info["ExperimentTime"]).isoformat()
    attributes['FILEPROP.Name'] = name
    
    dic = {"Data": data, "Attributes": attributes}
    return dic