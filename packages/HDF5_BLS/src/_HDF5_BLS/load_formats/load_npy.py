import os
from typing import Optional, Dict, Any
import numpy as np

from .base import BaseLoaderPlugin, ImportPayload


class NpyPlugin(BaseLoaderPlugin):
    id = "npy_loader"
    name = "NumPy Array Loader"
    description = "Loads binary NumPy array (.npy) files."
    supported_extensions = [".npy"]

    def load(
        self,
        filepath: str,
        parameters: Optional[Dict[str, Any]] = None,
        brillouin_type: Optional[str] = None
    ) -> ImportPayload:
        brillouin_type = brillouin_type or "Raw_data"
        data = np.load(filepath)
        name = ".".join(os.path.basename(filepath).split(".")[:-1])
        attributes = {"FILEPROP.Name": name}

        payload = ImportPayload(attributes=attributes)
        payload.add_dataset(name=brillouin_type, data=data, dataset_type=brillouin_type)
        return payload


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
    return NpyPlugin().load(filepath, brillouin_type=brillouin_type)
