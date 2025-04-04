import os

from HDF5_BLS.load_formats.errors import LoadError_creator, LoadError_parameters

###############################################################################
# GENERAL GUIDELINES
    # This file is meant to dispatch the loading of the data to the sub-module load_formats. 
    # This sub-module is classified in types of files and for each file, one or more functions are defined, depending on the user's needs.
    # All the functions return a dictionnary with two minimal keys: "Data" and "Attributes". 
    # The "Data" key contains the data and the "Attributes" key contains the attributes of the file.
    # The attributes are stored in a dictionnary and their names can be found in the "spreadsheet" folder of the repository
    # Additionally, other keys can be found in the returned dictionnary, depending on the technique used.

# GUIDELINES FOR GUI COMPATIBILITY:
    # If you need to load your files with a specific process, please add the parameter "creator" to the function set to None by default. Then if the function is called without any creator, have the function raise a LoadError_creator exception with the list of creators that can be used to load the data (an example is given in load_dat_file).
    # If the data has to be loaded with parameters, define the function with an additional parameter "parameters" set to None by default. Then if the function is called without any parameters, have the function raise a LoadError_parameters exception with the list of parameters that can be used to load the data (an example is found in load_formats/load_dat.py in function load_dat_TimeDomain).
###############################################################################


def load_dat_file(filepath, creator = None, parameters = None): # Test made for GHOST
    """Loads DAT files. The DAT files that can be read are obtained from the following configurations:
    - GHOST software
    - Time Domain measures

    Parameters
    ----------
    filepath : str                           
        The filepath to the GHOST file
    creator : str, optional
        The way this dat file has to be loaded. If None, an error is raised. Possible values are:
        - "GHOST": the file is assumed to be a GHOST file
        - "TimeDomain": the file is assumed to be a TimeDomain file
    
    Returns
    -------
    dict
        The dictionnary with the data and the attributes of the file stored respectively in the keys "Data" and "Attributes". For time domain files, the dictionnary also contains the time vector in the key "Abscissa_dt".
    """
    from HDF5_BLS.load_formats.load_dat import load_dat_GHOST, load_dat_TimeDomain

    if creator == "GHOST": return load_dat_GHOST(filepath)
    elif creator == "TimeDomain": return load_dat_TimeDomain(filepath, parameters)
    else:
        creator_list = ["GHOST", "TimeDomain"]
        raise LoadError_creator(f"Unsupported creator {creator}, accepted values are: {', '.join(creator_list)}", creator_list)

def load_image_file(filepath, parameters = None): # Test made
    """Loads image files using Pillow

    Parameters
    ----------
    filepath : str                           
        The filepath to the image
    
    Returns
    -------
    dict
        The dictionnary with the data and the attributes of the file stored respectively in the keys "Data" and "Attributes"
    """
    from HDF5_BLS.load_formats.load_image import load_image_base
    return load_image_base(filepath, parameters = parameters)

def load_npy_file(filepath): # Test made
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
    from HDF5_BLS.load_formats.load_npy import load_npy_base
    return load_npy_base(filepath)

def load_sif_file(filepath, parameters = None): 
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
    from HDF5_BLS.load_formats.load_sif import load_sif_base
    return load_sif_base(filepath, parameters = parameters)

def load_general(filepath, creator = None, parameters = None): # Test made 
    """Loads files based on their extensions

    Parameters
    ----------
    filepath : str                           
        The filepath to the file
    
    Returns
    -------
    dict
        The dictionnary created with the given filepath and eventually parameters.
    """
    _, file_extension = os.path.splitext(filepath)
    
    if file_extension.lower() == ".dat":
        # Load .DAT file format data
        return load_dat_file(filepath, creator = creator, parameters = parameters)
    elif file_extension.lower() in ['.apng', '.blp', '.bmp', '.bw', '.cur', '.dcx', '.dds', '.dib', '.emf', '.eps', '.fit', '.fits', '.flc', '.fli', '.ftc', '.ftu', '.gbr', '.gif', '.hdf', '.icb', '.icns', '.ico', '.iim', '.im', '.j2c', '.j2k', '.jfif', '.jp2', '.jpc', '.jpe', '.jpeg', '.jpf', '.jpg', '.jpx', '.mpg', '.msp', '.pbm', '.pcd', '.pcx', '.pfm', '.pgm', '.png', '.pnm', '.ppm', '.ps', '.psd', '.pxr', '.qoi', '.ras', '.rgb', '.rgba', '.sgi', '.tga', '.tif', '.tiff', '.vda', '.vst', '.webp', '.wmf', '.xbm', '.xpm']:
        # Load image files
        return load_image_file(filepath, parameters = parameters)
    elif file_extension.lower() == ".npy":
        # Load .npy file format data
        return load_npy_file(filepath)
    elif file_extension.lower() == ".sif":
        # Load .npy file format data
        return load_sif_file(filepath, parameters = parameters)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")