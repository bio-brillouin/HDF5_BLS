import os
from PIL import Image
import numpy as np


def load_tiff_base(filepath):
    """Loads files obtained with the GHOST software

    Parameters
    ----------
    filepath : str                           
        The filepath to the tif image
    
    Returns
    -------
    dict
        The dictionnary with the data and the attributes of the file stored respectively in the keys "Data" and "Attributes"
    """
    data = []
    name, _ = os.path.splitext(filepath)
    attributes = {}

    im = Image.open(filepath)
    data = np.array(im)

    name = ".".join(os.path.basename(filepath).split(".")[:-1])
    attributes['FILEPROP.Name'] = name

    dic = {"Data": data, "Attributes": attributes}
    return dic