import os
import numpy as np

def load_npy_base(filepath, brillouin_type = "Raw_data"):
    """Loads npy files

    Parameters
    ----------
    filepath : str                           
        The filepath to the npy file
    brillouin_type : str, optional
        The brillouin type of the file. Default is "Raw_data"
    
    Returns
    -------
    dict
        The dictionary with the data and the attributes of the file stored respectively in the keys "Data" and "Attributes"
    """
    data = np.load(filepath)
    attributes = {}
    name = ".".join(os.path.basename(filepath).split(".")[:-1])
    attributes['FILEPROP.Name'] = name

    dic = {brillouin_type:{"Name": "Raw_data", "Data": data}, 
           "Attributes": attributes}
    return dic
