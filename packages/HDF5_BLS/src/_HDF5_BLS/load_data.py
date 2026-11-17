import os
import sys 

###############################################################################
# GENERAL GUIDELINES
    # This file is meant to dispatch the loading of the data to the sub-module load_formats. 
    # This sub-module is classified in types of files and for each file, one or more functions are defined, depending on the user's needs.
    # All the functions return a dictionary with two minimal keys: "Data" and "Attributes". 
    # The "Data" key contains the data and the "Attributes" key contains the attributes of the file.
    # The attributes are stored in a dictionary and their names can be found in the "spreadsheet" folder of the repository
    # Additionally, other keys can be found in the returned dictionary, depending on the technique used.

# GUIDELINES FOR GUI COMPATIBILITY:
    # If you need to load your files with a specific process, please add the parameter "creator" to the function set to None by default. Then if the function is called without any creator, have the function raise a LoadError_creator exception with the list of creators that can be used to load the data (an example is given in load_dat_file).
    # If the data has to be loaded with parameters, define the function with an additional parameter "parameters" set to None by default. Then if the function is called without any parameters, have the function raise a LoadError_parameters exception with the list of parameters that can be used to load the data (an example is found in load_formats/load_dat.py in function load_dat_TimeDomain).
###############################################################################


from .load_formats.registry import get_registry, register_loader, add_plugin_directory
from .load_formats.base import BaseLoaderPlugin, ImportPayload, ParameterSpec
from .load_formats.load_errors import (
    LoadError,
    LoadError_creator,
    LoadError_parameters,
    PluginNotFoundError,
    AmbiguousPluginError,
    InvalidParameterError,
    PluginExecutionError,
)


def load_dat_file(filepath, creator = None, parameters = None, brillouin_type = None):
    """Loads DAT files using registered plugins."""
    return load_general(filepath, creator = creator, parameters = parameters, brillouin_type = brillouin_type)


def load_image_file(filepath, parameters = None, brillouin_type = None):
    """Loads image files using registered plugins."""
    return load_general(filepath, parameters = parameters, brillouin_type = brillouin_type)


def load_npy_file(filepath, brillouin_type = None):
    """Loads npy files using registered plugins."""
    return load_general(filepath, brillouin_type = brillouin_type)


def load_sif_file(filepath, parameters = None, brillouin_type = None):
    """Loads sif files using registered plugins."""
    return load_general(filepath, parameters = parameters, brillouin_type = brillouin_type)


def load_general(filepath, creator = None, parameters = None, brillouin_type = None):
    """Loads files using the plugin loading platform based on extension, sniffing, or creator.

    Parameters
    ----------
    filepath : str                           
        The filepath to the file to load
    creator : str, optional
        An argument to specify how the data was created or select a specific plugin.
    parameters : dict, optional
        A dictionary containing format-specific parameters.
    brillouin_type : str, optional
        The Brillouin type of the dataset to load.
    
    Returns
    -------
    ImportPayload
        The container containing loaded datasets and metadata attributes (compatible with standard dict access).
    """
    registry = get_registry()
    return registry.load(filepath, creator = creator, parameters = parameters, brillouin_type = brillouin_type)