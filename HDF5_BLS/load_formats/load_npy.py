import os
import numpy as np

def load_npy_base(filepath):
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
    data = np.load(filepath)
    attributes = {}
    name = ".".join(os.path.basename(filepath).split(".")[:-1])
    attributes['FILEPROP.Name'] = name

    dic = {"Data": data, "Attributes": attributes}
    return dic
