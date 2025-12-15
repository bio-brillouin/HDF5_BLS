import os
from PIL import Image
import numpy as np


def load_image_base(filepath, parameters = None, brillouin_type = "Raw_data"):
    """Loads image files with the Pillow library. Note that by default the Brillouin type is "Raw data". Please specify the Brillouin type in the parameters if you want to change it.

    Parameters
    ----------
    filepath : str                           
        The filepath to the tif image
    parameters : dict, optional
        A dictionary with the parameters to load the data, by default None. Please refer to the Note section of this docstring for more information.
    
    Returns
    -------
    dict
        The dictionary with the data and the attributes of the file stored respectively in the keys "Data" and "Attributes"
    
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
        if "Grayscale" in parameters.keys() and parameters["Grayscale"]: 
            data = np.mean(data, axis = 2)

    dic = {brillouin_type: {"Name": "Raw data", "Data": data}, 
           "Attributes": attributes}
    return dic