import h5py
import numpy as np
import csv
import os
from PIL import Image

try:
    from Load_data import Load_Data
except:
    from src.Load_data import Load_Data
    

BLS_HDF5_Version = 0.1

class Wraper:
    def __init__(self):
        self.filepath = None
        self.attributes = {}
        self.abscissa = None
        self.raw_data = None
        self.calibration_curve = None
        self.impulse_response = None
        self.loader = Load_Data()

    def define_abscissa_1D(self, min_val, max_val, nb_samples):
        """Defines a new abscissa axis based on min, max values, and number of samples.
    
        Parameters
        ----------
        min_val : float                           
            First point of the abscissa
        max_val : float                           
            Last point of the abscissa
        nb_sambles : float                           
            Number of samples in the abscissa
        
        Returns
        -------
        self.abscissa : numpy array
            The abscissa values
        """
        self.abscissa = np.linspace(min_val, max_val, nb_samples)
        return self.abscissa

    def export_properties_data(self, filepath_csv):
        """Exports properties to a CSV file. This csv is meant to be made once to store all the properties of the spectrometer and then minimally adjusted to the sample being measured.
    
        Parameters
        ----------
        filepath_csv : str                           
            The filepath to the csv storing the properties of the measure. 
        
        Returns
        -------
        boolean : boolean
            True if the file was exported properly, false if an error occured.
        """
        try:
            with open(filepath_csv, mode='w', newline='') as csv_file:
                csv_writer = csv.writer(csv_file)
                for key, value in self.attributes.items():
                    csv_writer.writerow([key, value])
            return True
        except:
            return False

    def import_abscissa(self, filepath):
        """Imports abscissa points from a file and returns the associated array.
    
        Parameters
        ----------
        filepath : str                           
            The filepath to the values of the abscissa
        
        Returns
        -------
        self.abscissa : numpy array
            The numpy array corresponding to the abscissa being imported
        """
        self.abscissa, _ = self.loader.load_general(filepath)
        return self.abscissa
  
    def import_properties_data(self, filepath):
        """Imports properties from a CSV file into a dictionary.
    
        Parameters
        ----------
        filepath_csv : str                           
            The filepath to the csv storing the properties of the measure. This csv is meant to be made once to store all the properties of the spectrometer and then minimally adjusted to the sample being measured.
        
        Returns
        -------
        self.attributes : dic
            The dictionnary containing all the attributes
        """
        with open(filepath, mode='r') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                key, value = row
                self.attributes[key] = value
        return self.attributes

    def open_calibration(self, filepath):
        """Opens a calibration curve file and returns the calibration curve.
    
        Parameters
        ----------
        filepath : str                           
            The filepath to the calibration curve
        
        Returns
        -------
        self.calibration_curve : numpy array
            The numpy array corresponding to the calibration curve
        """
        self.calibration_curve, _ = self.loader.load_general(filepath)
        return self.calibration_curve

    def open_hdf5_files(self, filepath):
        """Opens a hdf5 file
    
        Parameters
        ----------
        filepath : str                           
            The filepath to the hdf5 file
        
        Returns
        -------
        self.data : numpy array
            The numpy array corresponding to the data of the hdf5 file
        self.attributes: dic
            The dictionnary containing all the attributes of the hdf5 file opened
        """
        return self.loader.load_hdf5_file(filepath)

    def open_data(self, filepath):
        """Opens a raw data file based on its file extension and stores the filepath.
    
        Parameters
        ----------
        filepath : str                           
            The filepath to the raw data file
        
        Returns
        -------
        self.data : numpy array
            The numpy array corresponding to the data of the hdf5 file
        self.attributes: dic
            The dictionnary containing all the attributes of the hdf5 file opened
        """
        self.filepath = filepath
        self.data, self.attributes = self.loader.load_general(filepath)
        
        return self.data, self.attributes

    def open_IR(self, filepath):
        """Opens an impulse response file and returns the curve.
    
        Parameters
        ----------
        filepath : str                           
            The filepath to the impulse response curve
        
        Returns
        -------
        self.impulse_response : numpy array
            The numpy array corresponding to the impulse response curve
        """
        self.impulse_response, _ = self.loader.load_general(filepath)
        return self.impulse_response

    def properties_data(self, **kwargs):
        """Creates a dictionary with the given properties.
    
        Parameters
        ----------
        **kwargs : dic, optional                           
            The arguments to update or set the attributes of the hdf5 file.
        
        Returns
        -------
        self.attributes : dic
            The dictionnary containing all the attributes of the hdf5 file
        """
        self.attributes = kwargs
        return self.attributes

    def save_hdf5_as(self, filepath):
        """Saves the data and attributes to an HDF5 file.
    
        Parameters
        ----------
        save_filepath : str                           
            The filepath where to save the hdf5 file
        
        Returns
        -------
        boolean : boolean
            True if the file was saved correctly, False if not
        """
        try:
            with h5py.File(filepath, 'w') as hdf5_file:
                # Save attributes
                for key, value in self.attributes.items():
                    hdf5_file.attrs[key] = value
                
                # Save datasets if they exist
                if self.raw_data is not None:
                    hdf5_file.create_dataset('Raw_Data', data=self.raw_data)
                    print("added Raw data")
                if self.abscissa is not None:
                    hdf5_file.create_dataset('Abscissa', data=self.abscissa)
                if self.calibration_curve is not None:
                    hdf5_file.create_dataset('Calibration_Curve', data=self.calibration_curve)
                if self.impulse_response is not None:
                    hdf5_file.create_dataset('Impulse_Response', data=self.impulse_response)
            return True
        except:
            return False

