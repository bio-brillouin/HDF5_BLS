
from configparser import ConfigParser
import numpy as np
import os
from PIL import Image
import h5py

config = ConfigParser()
config.read(["HDF5_BLS/config.ini", "config.ini"])

BLS_HDF5_Version = config["General"]["version_hdf5_bls"]

class Load_Data():
    def __init__(self):
        pass

    def load_dat_file(self, filepath):
        """Loads files obtained with the GHOST software
    
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
        attributes['FILEPROP.BLS_HDF5_Version'] = BLS_HDF5_Version
        attributes['FILEPROP.Name'] = name
        attributes['MEASURE.Sample'] = metadata["Sample"]
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

    def load_tiff_file(self, filepath):
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

        attributes['FILEPROP.BLS_HDF5_Version'] = BLS_HDF5_Version
        attributes['FILEPROP.Name'] = name

        return data, attributes

    def load_hdf5_file(self, filepath):
        """Loads HDF5 files
    
        Parameters
        ----------
        filepath : str                           
            The filepath to the HDF5 file
        
        Returns
        -------
        data : np.array
            The data stored in the file
        attributes : dic
            A dictionnary with all the properties that could be recovered from the file
        """
        attributes = {}
        with h5py.File(filepath, 'r') as hdf5_file:
            data = hdf5_file["Raw_Data"][:]
            
            for key in hdf5_file.attrs.keys():
                attributes[key] = hdf5_file.attrs[key]
            
        return data, attributes

    def load_general(self, filepath):
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
            return self.load_dat_file(filepath)
        elif file_extension.lower() == ".tif":
            # Load .TIFF file format data
            return self.load_tiff_file(filepath)
        elif file_extension.lower() == ".h5":
            # Load .TIFF file format data
            return self.load_hdf5_file(filepath)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")