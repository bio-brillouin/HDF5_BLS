
import numpy as np
import os
from PIL import Image
import h5py
import sif_parser
from datetime import datetime

def load_dat_file(filepath, creator = "GHOST"): # Test made for GHOST
    """Loads DAT files. The DAT files that can be read are obtained from the following configurations:
    - GHOST software
    - local exports with header

    Parameters
    ----------
    filepath : str                           
        The filepath to the GHOST file
    
    Returns
    -------
    data : np.array
        The data stored in the file
    attributes : dic
        A dictionnary with all the properties that could be recovered from the file
    """
    metadata = {}
    data = []
    name, _ = os.path.splitext(filepath)
    attributes = {}
    
    if creator == "GHOST":
        with open(filepath, 'r') as file:
            lines = file.readlines()
            # Extract metadata
            for line in lines:
                if line.strip() == '':
                    continue  # Skip empty lines
                if any(char.isdigit() for char in line.split()[0]):
                    break  # Stop at the first number
                else:
                    # Split metadata into key-value pairs
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
            # Extract numerical data
            for line in lines:
                if line.strip().isdigit():
                    data.append(int(line.strip()))

        data = np.array(data)
        attributes['FILEPROP.Name'] = name.split("/")[-1]
        attributes['MEASURE.Sample'] = metadata["Sample"]
        attributes['MEASURE.Date'] = ""
        attributes['SPECTROMETER.Scanning_Strategy'] = "point_scanning"
        attributes['SPECTROMETER.Type'] = "TFP"
        attributes['SPECTROMETER.Illumination_Type'] = "CW"
        attributes['SPECTROMETER.Detector_Type'] = "Photon Counter"
        attributes['SPECTROMETER.Filtering_Module'] = "None"
        attributes['SPECTROMETER.Wavelength_nm'] = metadata["Wavelength"]
        attributes['SPECTROMETER.Scan_Amplitude'] = metadata["Scan amplitude"]
        spectral_resolution = float(float(metadata["Scan amplitude"])/data.shape[-1])
        attributes['SPECTROMETER.Spectral_Resolution'] = str(spectral_resolution)
        return data, attributes

def load_tiff_file(filepath): # Test made
    """Loads files obtained with the GHOST software

    Parameters
    ----------
    filepath : str                           
        The filepath to the tif image
    
    Returns
    -------
    data : np.array
        The data stored in the file
    attributes : dic
        A dictionnary with all the properties that could be recovered from the file
    """
    data = []
    name, _ = os.path.splitext(filepath)
    attributes = {}

    im = Image.open(filepath)
    data = np.array(im)

    name = ".".join(os.path.basename(filepath).split(".")[:-1])
    attributes['FILEPROP.Name'] = name

    return data, attributes

def load_npy_file(filepath): # Test made
    """Loads npy files

    Parameters
    ----------
    filepath : str                           
        The filepath to the npy file
    
    Returns
    -------
    data : np.array
        The data stored in the file
    attributes : dic
        A dictionnary with all the properties that could be recovered from the file
    """
    data = np.load(filepath)
    attributes = {}
    name = ".".join(os.path.basename(filepath).split(".")[:-1])
    attributes['FILEPROP.Name'] = name
    return data, attributes

def load_sif_file(filepath): 
    """Loads npy files

    Parameters
    ----------
    filepath : str                           
        The filepath to the npy file
    
    Returns
    -------
    data : np.array
        The data stored in the file
    attributes : dic
        A dictionnary with all the properties that could be recovered from the file
    """
    metadata = {}
    name, _ = os.path.splitext(filepath)
    attributes = {}

    data, info = sif_parser.np_open(filepath)


    attributes['MEASURE.Exposure_s'] = str(info["ExposureTime"])
    attributes['SPECTROMETER.Detector_Model'] = info["DetectorType"]
    attributes['MEASURE.Date_of_measure'] = datetime.fromtimestamp(info["ExperimentTime"]).isoformat()

    if data.shape[0] == 1:
        data = data[0]

    return data, attributes

def load_general(filepath): # Test made 
    """Loads files based on their extensions

    Parameters
    ----------
    filepath : str                           
        The filepath to the file
    
    Returns
    -------
    data : np.array
        The data stored in the file
    attributes : dic
        A dictionnary with all the properties that could be recovered from the file
    """
    _, file_extension = os.path.splitext(filepath)
    
    if file_extension.lower() == ".dat":
        # Load .DAT file format data
        return load_dat_file(filepath)
    elif file_extension.lower() == ".tif":
        # Load .TIFF file format data
        return load_tiff_file(filepath)
    elif file_extension.lower() == ".npy":
        # Load .npy file format data
        return load_npy_file(filepath)
    elif file_extension.lower() == ".sif":
        # Load .npy file format data
        return load_sif_file(filepath)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")