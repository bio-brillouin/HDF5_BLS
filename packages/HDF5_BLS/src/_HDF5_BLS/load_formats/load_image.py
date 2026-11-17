import os
from typing import Optional, Dict, Any
from PIL import Image
import numpy as np

from .base import BaseLoaderPlugin, ImportPayload, ParameterSpec

IMAGE_EXTENSIONS = [
    '.apng', '.blp', '.bmp', '.bw', '.cur', '.dcx', '.dds', '.dib', '.emf', '.eps',
    '.fit', '.fits', '.flc', '.fli', '.ftc', '.ftu', '.gbr', '.gif', '.hdf', '.icb',
    '.icns', '.ico', '.iim', '.im', '.j2c', '.j2k', '.jfif', '.jp2', '.jpc', '.jpe',
    '.jpeg', '.jpf', '.jpg', '.jpx', '.mpg', '.msp', '.pbm', '.pcd', '.pcx', '.pfm',
    '.pgm', '.png', '.pnm', '.ppm', '.ps', '.psd', '.pxr', '.qoi', '.ras', '.rgb',
    '.rgba', '.sgi', '.tga', '.tif', '.tiff', '.vda', '.vst', '.webp', '.wmf', '.xbm', '.xpm'
]


class ImagePlugin(BaseLoaderPlugin):
    id = "image_loader"
    name = "Pillow Image Loader"
    description = "Loads raster image files supported by the Pillow library."
    supported_extensions = IMAGE_EXTENSIONS
    parameter_specs = {
        "grayscale": ParameterSpec(
            name="grayscale",
            type=bool,
            default=False,
            description="If True, converts image to grayscale by averaging color channels.",
        ),
        "Grayscale": ParameterSpec(
            name="Grayscale",
            type=bool,
            default=False,
            description="Alias for grayscale.",
        ),
    }

    def load(
        self,
        filepath: str,
        parameters: Optional[Dict[str, Any]] = None,
        brillouin_type: Optional[str] = None
    ) -> ImportPayload:
        im = Image.open(filepath)
        data = np.array(im)

        name = ".".join(os.path.basename(filepath).split(".")[:-1])
        attributes = {'FILEPROP.Name': name}

        if parameters is not None:
            grayscale = parameters.get("grayscale") or parameters.get("Grayscale", False)
            if grayscale and data.ndim == 3:
                data = np.mean(data, axis=2)

        dataset_key = brillouin_type or "Raw_data"
        payload = ImportPayload(attributes=attributes)
        payload.add_dataset(name=dataset_key, data=data, dataset_type=dataset_key)
        return payload


def load_image_base(filepath, parameters = None, brillouin_type = "Raw_data"):
    """Loads image files with the Pillow library. Note that by default the Brillouin type is "Raw data". Please specify the Brillouin type in the parameters if you want to change it.

    Parameters
    ----------
    filepath : str                           
        The filepath to the tif image
    parameters : dict, optional
        A dictionary with the parameters to load the data, by default None. Please refer to the Note section of this docstring for more information.
    brillouin_type : str, optional
        The Brillouin type of the dataset to add, by default "Raw_data"
    
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
    return ImagePlugin().load(filepath, parameters=parameters, brillouin_type=brillouin_type)