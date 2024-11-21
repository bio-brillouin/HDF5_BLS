import h5py
import numpy as np
import csv
import os
from PIL import Image

try:
    from Load_data import load_general, load_dat_file, load_hdf5_file, load_tiff_file
except:
    from HDF5_BLS.Load_data import load_general, load_dat_file, load_hdf5_file, load_tiff_file
    

BLS_HDF5_Version = 0.1

class WraperError(Exception):
    def __init__(self, msg) -> None:
        self.message = msg
        super().__init__(self.message)

class Wraper:
    """
    This object is used to store data and attributes in a unified structure.

    Attributes
    ----------
    attributes: dic
        The attributes of the data
    data: dic
        The data arrays (raw data, treated data, abscissa, other measures)
    data_attributes: dic
        The attributes specific to an array
    """
    def __init__(self, attributes = {}, data = {}):
        self.attributes = attributes # Dictionnary storing all the attributes
        self.data = data # Dictionnary storing all the datasets or wraper objects, group "Data" of HDF5 file
        self.data_attributes = {}

    def open_data(self, filepath, store_filepath = True):
        """Opens a raw data file based on its file extension and stores the filepath.
    
        Parameters
        ----------
        filepath : str                           
            The filepath to the raw data file
        store_filepath: bool, default True
            A boolean parameter to store the original filepath of the raw data in the attributes of "Raw_data"
        """
        # Opens the raw file and retrieve the retrievable attributes
        data, attributes = load_general(filepath)

        # Add the raw data to the "Raw_data" dataset of the wrapper and writes the dimensionnality of the data
        self.data["Raw_data"] = data
        self.data_attributes["Raw_data"] = {"ID":"Raw_data"}
        if store_filepath: self.data_attributes["Raw_data"]["Filepath"] = True
        self.attributes["MEASURE.Dimensionnality_of_measure"]=len(data.shape)
        
        # Generate the abscissa corresponding to the different dimensions
        abscissa_name = ""
        for i, k in enumerate(data.shape):
            self.data[f"Abscissa_{i}"] = np.arange(k)
            self.data_attributes[f"Abscissa_{i}"] = {"ID":f"Abscissa_{i}"}
            abscissa_name = abscissa_name+"_,"
        self.attributes["MEASURE.Abscissa_Names"] = abscissa_name[:-1]
        
        # Storing the retrieved attributes
        self.attributes = attributes

    def assign_name_all_abscissa(self, abscissa):
        """Adds as attributes of the abscissas and the raw data, the names of the abscissas

        Parameters
        ----------
        abscissa : str
            The names of the abscissas
        
        Raises
        ------
        WraperError
            If the length of the abscissa is different from the dimensionality of the data.
        """
        # Adds the names of the abscissas to the attributes of the Raw data
        abscissa = abscissa.split(",")
        if len(abscissa) != len(self.data["Raw_data"].shape):
            raise WraperError("The names provided for the abscissa do not match the shape of the raw data")
        else:
            for i, e in enumerate(abscissa):
                self.data_attributes[f"Abscissa_{i}"]["Name"] = e 
            self.attributes["MEASURE.Abscissa_Names"] = ','.join(abscissa)

    def create_abscissa_1D_min_max(self, dimension, min, max, name = None):
        """Creates an abscissa from a minimal and maximal value

        Parameters
        ----------
        dimension : int
            The dimension of the data that we are changing (first dimension is 0)
        min : float
            The minimal value of the abscissa range (included)
        max : float
            The maximal value of the abscissa range (included)
        name : str, optional
            The name of the abscissa axis, by default None

        Raises
        ------
        WraperError
            If the dimension given is higher than the dimension of the data
        """
        if dimension >= len(self.data["Raw_data"].shape):
            raise WraperError("The dimension provided for the abscissa is too large considering the size of the raw data")
        self.data[f"Abscissa_{dimension}"] = np.linspace(min, max, self.data["Raw_data"].shape[dimension])
        if not name is None:
            self.data_attributes[f"Abscissa_{dimension}"]["Name"] = name
            temp = self.attributes["MEASURE.Abscissa_Names"].split(",")
            temp[dimension] = name
            self.attributes["MEASURE.Abscissa_Names"] = ",".join(temp)
    
    def import_abscissa_1D(self, dimension, filepath, name = None):
        """Creates an abscissa from a minimal and maximal value

        Parameters
        ----------
        dimension : int
            The dimension of the data that we are changing (first dimension is 0)
        filepath : str
            The filepath containing the values of the abscissa
        name : str, optional
            The name of the abscissa axis, by default None
        
        Raises
        ------
        WraperError
            If the dimension given is higher than the dimension of the data
        """
        if dimension >= len(self.data["Raw_data"].shape):
            raise WraperError("The dimension provided for the abscissa is too large considering the size of the raw data")
        self.data[f"Abscissa_{dimension}"], _ = load_general(filepath)
        if not name is None:
            self.data_attributes[f"Abscissa_{dimension}"]["Name"] = name
            temp = self.attributes["MEASURE.Abscissa_Names"].split(",")
            temp[dimension] = name
            self.attributes["MEASURE.Abscissa_Names"] = ",".join(temp)



# def load_general(f):
#     return np.arange(10**4).reshape((10,10,10,10)), {}

# wrp = Wraper()
# wrp.open_data("")
# wrp.assign_name_all_abscissa("Position x, Position y, Position z, Channels")
# wrp.create_abscissa_1D_min_max(0,-10,10,"Position x new")
# print(wrp.attributes["MEASURE.Abscissa_Names"])
# print(wrp.data_attributes)
# print(wrp.data[f"Abscissa_{0}"])


    # def add_hdf5_to_wraper(self, filepath, parent_group = "Data"):
    #     """Adds an hdf5 file to the wrapper by specifying in which group the data have to be stored. Default is the "Data" group. When adding the data, the attributes of the HDF5 file are only added to the created group if they are different from the parent's attribute.

    #     Parameters
    #     ----------
    #     filepath : str
    #         The filepath of the hdf5 file to add.
    #     parent_group : str, optional
    #         The parent group where to store the data of the HDF5 file, by default the parent group, "Data". The format of this group should be "Data.Data_0.Data_0_0"
    #     Returns
    #     -------
    #     self.data : dic
    #         The dictionnary with the wraper object.
    #     """
    #     data, attributes = load_hdf5_file(filepath)
    #     wrp = Wraper(attributes, data)

    #     loc = parent_group.split(".")
    #     loc.pop(0)
    #     par = self.data 
    #     while len(loc)>0:
    #         temp = loc[0]
    #         try:
    #             par = par[temp]
    #         except:
    #             par[temp] = {}
    #             par = par[temp]
    #         loc.pop(0)
    #     par["Data"]["Raw_data"] = data
    #     par["Attributes"] = attributes
    #     return self.data

    # def define_frequency_1D(self, min_val, max_val, nb_samples):
    #     """Defines a frequency axis based on min, max values, and number of samples. Usable when the sampling frequency is precisely known, in TFP spectrometers for example.
    
    #     Parameters
    #     ----------
    #     min_val : float                           
    #         Frequency value of the first channel
    #     max_val : float                           
    #         Frequency value of the last channel
    #     nb_sambles : float                           
    #         Number of samples in the frequency array
        
    #     Returns
    #     -------
    #     self.frequency : numpy array
    #         The frequency array
    #     """
    #     self.frequency = np.linspace(min_val, max_val, nb_samples)
    #     return self.frequency

    # def export_properties_data(self, filepath_csv):
    #     """Exports properties to a CSV file. This csv is meant to be made once to store all the properties of the spectrometer and then minimally adjusted to the sample being measured.
    
    #     Parameters
    #     ----------
    #     filepath_csv : str                           
    #         The filepath to the csv storing the properties of the measure. 
        
    #     Returns
    #     -------
    #     boolean : boolean
    #         True if the file was exported properly, false if an error occured.
    #     """
    #     try:
    #         with open(filepath_csv, mode='w', newline='') as csv_file:
    #             csv_writer = csv.writer(csv_file)
    #             for key, value in self.attributes.items():
    #                 csv_writer.writerow([key, value])
    #         return True
    #     except:
    #         return False

    # def import_frequency(self, filepath):
    #     """Imports frequency points from a file and returns the associated array.
    
    #     Parameters
    #     ----------
    #     filepath : str                           
    #         The filepath to the values of the frequency array
        
    #     Returns
    #     -------
    #     self.frequency : numpy array
    #         The numpy array corresponding to the frequency being imported
    #     """
    #     self.frequency, _ = self.loader.load_general(filepath)
    #     return self.frequency
  
    # def import_properties_data(self, filepath):
    #     """Imports properties from a CSV file into a dictionary.
    
    #     Parameters
    #     ----------
    #     filepath_csv : str                           
    #         The filepath to the csv storing the properties of the measure. This csv is meant to be made once to store all the properties of the spectrometer and then minimally adjusted to the sample being measured.
        
    #     Returns
    #     -------
    #     self.attributes : dic
    #         The dictionnary containing all the attributes
    #     """
    #     with open(filepath, mode='r') as csv_file:
    #         csv_reader = csv.reader(csv_file)
    #         for row in csv_reader:
    #             key, value = row
    #             self.attributes[key] = value
    #     return self.attributes

    # def open_calibration(self, filepath):
    #     """Opens a calibration curve file and returns the calibration curve.
    
    #     Parameters
    #     ----------
    #     filepath : str                           
    #         The filepath to the calibration curve
        
    #     Returns
    #     -------
    #     self.calibration_curve : numpy array
    #         The numpy array corresponding to the calibration curve
    #     """
    #     self.calibration_curve, _ = self.loader.load_general(filepath)
    #     return self.calibration_curve

    # def open_hdf5_files(self, filepath):
    #     """Opens a hdf5 file
    
    #     Parameters
    #     ----------
    #     filepath : str                           
    #         The filepath to the hdf5 file
        
    #     Returns
    #     -------
    #     self.data : numpy array
    #         The numpy array corresponding to the data of the hdf5 file
    #     self.attributes: dic
    #         The dictionnary containing all the attributes of the hdf5 file opened
    #     """
    #     return self.loader.load_hdf5_file(filepath)

    # def open_IR(self, filepath):
    #     """Opens an impulse response file and returns the curve.
    
    #     Parameters
    #     ----------
    #     filepath : str                           
    #         The filepath to the impulse response curve
        
    #     Returns
    #     -------
    #     self.impulse_response : numpy array
    #         The numpy array corresponding to the impulse response curve
    #     """
    #     self.impulse_response, _ = self.loader.load_general(filepath)
    #     return self.impulse_response

    # def properties_data(self, **kwargs):
    #     """Creates a dictionary with the given properties.
    
    #     Parameters
    #     ----------
    #     **kwargs : dic, optional                           
    #         The arguments to update or set the attributes of the hdf5 file.
        
    #     Returns
    #     -------
    #     self.attributes : dic
    #         The dictionnary containing all the attributes of the hdf5 file
    #     """
    #     self.attributes = kwargs
    #     return self.attributes

    # def save_hdf5_as(self, filepath):
    #     """Saves the data and attributes to an HDF5 file.
    
    #     Parameters
    #     ----------
    #     save_filepath : str                           
    #         The filepath where to save the hdf5 file
        
    #     Returns
    #     -------
    #     boolean : boolean
    #         True if the file was saved correctly, False if not
    #     """
    #     try:
    #         with h5py.File(filepath, 'w') as hdf5_file:
    #             # Save attributes
    #             for key, value in self.attributes.items():
    #                 hdf5_file.attrs[key] = value
                
    #             # Create Data group
    #             data_group = hdf5_file.create_group("Data")

    #             # Save datasets if they exist
    #             if self.raw_data is not None:
    #                 data_group.create_dataset('Raw_data', data=self.raw_data)
    #             if self.frequency is not None:
    #                 data_group.create_dataset('Frequency', data=self.frequency)
    #             if self.calibration_curve is not None:
    #                 data_group.create_dataset('Calibration', data=self.calibration_curve)
    #             if self.impulse_response is not None:
    #                 data_group.create_dataset('Impulse_response', data=self.impulse_response)
    #         return True
    #     except:
    #         return False

