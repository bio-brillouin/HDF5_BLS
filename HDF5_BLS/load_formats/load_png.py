import os
from PIL import Image
import numpy as np


def load_png_base(filepath, parameters = None):
    """Loads files obtained with the GHOST software

    Parameters
    ----------
    filepath : str                           
        The filepath to the tif image
    parameters : dict, optional
        A dictionnary with the parameters to load the data, by default None. Please refer to the Note section of this docstring for more information.
    
    Returns
    -------
    dict
        The dictionnary with the data and the attributes of the file stored respectively in the keys "Data" and "Attributes"
    
    Note
    ----
    Possible parameters are:
    - grayscale: bool, optional
        If True, the image is converted to grayscale, by default False
    """
    data = []
    name, _ = os.path.splitext(filepath)
    attributes = {}

    im = Image.open(filepath)
    data = np.array(im)

    name = ".".join(os.path.basename(filepath).split(".")[:-1])
    attributes['FILEPROP.Name'] = name

    if parameters is not None:
        if "Grayscale" in parameters.keys() and parameters["Grayscale"]: data = np.mean(data, axis = 2)

    dic = {"Raw_data": {"Name": "Raw data", "Data": data}, 
           "Attributes": attributes}
    return dic