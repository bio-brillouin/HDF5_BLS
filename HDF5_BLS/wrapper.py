import h5py
import numpy as np
import csv
import os
from PIL import Image
import copy

try: # Used to patch an error in the generation of the documentation
    from load_data import load_general, load_dat_file, load_tiff_file
    from treat import Treat
except:
    from HDF5_BLS.load_data import load_general, load_dat_file, load_tiff_file
    from HDF5_BLS.treat import Treat
    

BLS_HDF5_Version = "0.0"

class WrapperError(Exception):
    def __init__(self, msg) -> None:
        self.message = msg
        super().__init__(self.message)

class Wrapper:
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
    def __init__(self, attributes = {}, data = {}, data_attributes = {}):
        self.attributes = attributes # Dictionnary storing all the attributes
        self.data = data # Dictionnary storing all the datasets or wrapper objects, group "Data" of HDF5 file
        self.data_attributes = data_attributes # Dictionnary storing all the attributes of all the data elements

    def add_hdf5_to_wrapper(self, filepath, parent_group = "Data", create_group = True):
        """Adds an hdf5 file to the wrapper by specifying in which group the data have to be stored. Default is the "Data" group. When adding the data, the attributes of the HDF5 file are only added to the created group if they are different from the parent's attribute.

        Parameters
        ----------
        filepath : str
            The filepath of the hdf5 file to add.
        parent_group : str, optional
            The parent group where to store the data of the HDF5 file, by default the parent group is the top group "Data". The format of this group should be "Data.Data_0.Data_0_0"
        create_group : bool, default True
            This parameter should be set to False if different techniques were used to acquire different datasets. This is particularly usefull if fluorescent images are taken after or during the same experiment. Note that only data of same shape, and sharing the same abscissa can be used in a given group. 
        """
        # Create a wrapper object with the contents of the hdf5 file
        wrp_h5 = load_hdf5_file(filepath)

        # Find the position where to add the spectrum
        loc = parent_group.split(".")
        loc.pop(0)
        par = self.data 

        while len(loc)>0:
            temp = loc[0]
            try:
                par = par[temp]
            except:
                par[temp] = {}
                par = par[temp]
            loc.pop(0)

        # Inspects the structure of the parent group and decides if to create a sub-group or not based on the create_group parameter
        if "Data_0" in par.keys():
            i = 0
            while f"Data_{i}" in par.keys():
                i+=1
            par[f"Data_{i}"] = wrp_h5
        else:
            self.attributes, self.data, self.data_attributes = merge_wrappers([self,wrp_h5])

    def assign_name_all_abscissa(self, abscissa):
        """Adds as attributes of the abscissas and the raw data, the names of the abscissas

        Parameters
        ----------
        abscissa : str
            The names of the abscissas
        
        Raises
        ------
        WrapperError
            If the length of the abscissa is different from the dimensionality of the data.
        """
        # Adds the names of the abscissas to the attributes of the Raw data
        abscissa = abscissa.split(",")
        if len(abscissa) != len(self.data["Raw_data"].shape):
            raise WrapperError("The names provided for the abscissa do not match the shape of the raw data")
        else:
            for i, e in enumerate(abscissa):
                self.data_attributes[f"Abscissa_{i}"]["Name"] = e 
            self.attributes["MEASURE.Abscissa_Names"] = ','.join(abscissa)
        
    def assign_name_one_abscissa(self, abscissa_nb, name):
        """Adds as attributes of the abscissas and the raw data, the names of the abscissas

        Parameters
        ----------
        abscissa_nb : str
            The number of the abscissa to rename ("i" or "i-j")
        name : str
            The new name of the abscissa to rename
        """
        # Adds the names of the abscissas to the attributes of the Raw data
        abscissa = []
        for k in self.data_attributes.keys():
            if k.split("_")[-1] == abscissa_nb:
                self.data_attributes[f"Abscissa_{abscissa_nb}"]["Name"] = name
            abscissa.append(self.data_attributes[f"Abscissa_{abscissa_nb}"]["Name"])
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
        WrapperError
            If the dimension given is higher than the dimension of the data
        """
        if dimension >= len(self.data["Raw_data"].shape):
            raise WrapperError("The dimension provided for the abscissa is too large considering the size of the raw data")
        self.data[f"Abscissa_{dimension}"] = np.linspace(min, max, self.data["Raw_data"].shape[dimension])
        if not name is None:
            self.data_attributes[f"Abscissa_{dimension}"]["Name"] = name
            temp = self.attributes["MEASURE.Abscissa_Names"].split(",")
            temp[dimension] = name
            self.attributes["MEASURE.Abscissa_Names"] = ",".join(temp)
        else:
            self.data_attributes[f"Abscissa_{dimension}"]["Name"] = "Abscissa"
            temp = self.attributes["MEASURE.Abscissa_Names"].split(",")
            temp[dimension] = "Abscissa"
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
        WrapperError
            If the dimension given is higher than the dimension of the data
        """
        if dimension >= len(self.data["Raw_data"].shape):
            raise WrapperError("The dimension provided for the abscissa is too large considering the size of the raw data")
        self.data[f"Abscissa_{dimension}"], _ = load_general(filepath)
        if not name is None:
            self.data_attributes[f"Abscissa_{dimension}"]["Name"] = name
            temp = self.attributes["MEASURE.Abscissa_Names"].split(",")
            temp[dimension] = name
            self.attributes["MEASURE.Abscissa_Names"] = ",".join(temp)

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
                category, key, value = row
                if category != '':
                    self.attributes[f"{category}.{key}"] = value
        return self.attributes

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
        data, attributes = load_general(self, filepath)

        # Add the raw data to the "Raw_data" dataset of the wrapper and writes the dimensionnality of the data
        self.data["Raw_data"] = data
        self.data_attributes["Raw_data"] = {"ID":"Raw_data"}
        if store_filepath: self.data_attributes["Raw_data"]["Filepath"] = filepath
        attributes["MEASURE.Dimensionnality_of_measure"]=len(data.shape)
        self.data_attributes["Raw_data"]["Name"] = "Raw data"
        
        # Generate the abscissa corresponding to the different dimensions
        abscissa_name = ""
        for i, k in enumerate(data.shape):
            self.data[f"Abscissa_{i}"] = np.arange(k)
            self.data_attributes[f"Abscissa_{i}"] = {"ID":f"Abscissa_{i}"}
            abscissa_name = abscissa_name+"_,"
        attributes["MEASURE.Abscissa_Names"] = abscissa_name[:-1]

        #Indicates the version of the BLS_HDF5 library
        attributes["FILEPROP.BLS_HDF5_Version"] = BLS_HDF5_Version
        
        # Storing the retrieved attributes
        self.attributes = attributes

    def save_as_hdf5(self,filepath):
        """Saves the data and attributes to an HDF5 file.
    
        Parameters
        ----------
        save_filepath : str                           
            The filepath where to save the hdf5 file
        
        Raises
        -------
        WrapperError
            Raises an error if the file could not be saved
        """
        def save_group(parent, group, id_group):
            data_group = parent.create_group(id_group)
            for key, value in group.attributes.items():
                data_group.attrs[key] = value
            for key in group.data.keys():
                if type(group.data[key]) == np.ndarray:
                    dg = data_group.create_dataset(key, data=group.data[key])
                    for k, v in group.data_attributes[key].items():
                        dg.attrs[k] = v
                elif type(group[key]) == Wrapper:
                    save_group(data_group, group[key], key)
                else:
                    raise WrapperError("Cannot add the selected type to HDF5 file")
                

        try:
            with h5py.File(filepath, 'w') as hdf5_file:
                # Save attributes
                for key, value in self.attributes.items():
                    hdf5_file.attrs[key] = value
                
                # Create Data group
                data_group = hdf5_file.create_group("Data")

                # Save datasets 
                for key in self.data.keys():
                    if type(self.data[key]) == np.ndarray:
                        dg = data_group.create_dataset(key, data=self.data[key])
                    elif type(self.data[key]) == Wrapper:
                        save_group(data_group, self.data[key], key)
                    else:
                        raise WrapperError("Cannot add the selected type to HDF5 file")
                    for k, v in self.data_attributes[key].items():
                        dg.attrs[k] = v
        except:
            raise WrapperError("The wrapper could not be saved as a HDF5 file")


def load_hdf5_file(filepath):
    """Loads HDF5 files

    Parameters
    ----------
    filepath : str                           
        The filepath to the HDF5 file
    
    Returns
    -------
    wrp : Wrapper
        The wrapper associated to the HDF5 file
    """
    def load_group(group):
        attributes = {}
        data_attributes = {}
        data = {}

        for k, v in group.items():
            if type(v) == h5py._hl.dataset.Dataset:
                data[k] = v
            elif type(v) == h5py._hl.group.Group:
                data[k] = load_group(v)
            else:
                raise WrapperError("Trying to add an object that is neither a group nor a dataset")
            data_attributes[k] = {}
            for ka, va in group[k].attrs.items():
                data_attributes[k][ka] = va
        for k, v in group.attrs.items():
            attributes[k] = v
        return Wrapper(attributes, data, data_attributes)
     
    attributes = {}
    data_attributes = {}
    data = {}
    with h5py.File(filepath, 'r') as hdf5_file:
        h5 = hdf5_file["Data"]
        for k, v in h5.items():
            if type(v) == h5py._hl.dataset.Dataset:
                data[k] = v
            elif type(v) == h5py._hl.group.Group:
                data[k] = load_group(v)
            else:
                raise WrapperError("Trying to add an object that is neither a group nor a dataset")
            data_attributes[k] = {}
            for ka, va in h5[k].attrs.items():
                data_attributes[k][ka] = va
    
        for k, v in hdf5_file.attrs.items():
            attributes[k] = v
        
    return Wrapper(attributes, data, data_attributes)

def merge_wrappers(list_wrappers, name = None, abscissa_from_attributes = None):
        """
        Merges a list of wrappers into a single wrapper, combining their common attributes.

        Parameters
        ----------
        list_wrappers : list of Wrapper objects
            The list of Wrapper objects to merge into a single Wrapper object.
        name: None or str, optional
            The name given to the file resulting of the merging of the wrappers
        abscissa_from_attributes: None or list of str, optional
            The name of the attributes from which to extract values to create an abscissa
        """
        # Initializing the parameters of the new wrapper
        attributes = list_wrappers[0].attributes.copy()
        data = {}
        data_attributes = {}

        # Extracting the common attributes
        for wrp in list_wrappers[1:]:
            old_attributes = attributes.copy()
            for k,v in old_attributes.items():
                if wrp.attributes[k] != v:
                    del attributes[k]

        # Deleting the common attributes of the individual wrappers and adding the remaining to data_attributes
        for i,wrp in enumerate(list_wrappers):
            l = list(attributes.keys())
            for k in l:
                del wrp.attributes[k]
            data_attributes[f"Data_{i}"] = wrp.attributes
        
        # Creating the new abscissa from the attributes of the wrappers
        if not abscissa_from_attributes is None:
            for i, ab in enumerate(abscissa_from_attributes):
                ab_temp = []
                for wrp in list_wrappers:
                    ab_temp.append(wrp.attributes[ab])
                try:
                    data[f"Abscissa_{i}"] = np.array(ab_temp).astype(float)
                    data_attributes[f"Abscissa_{i}"] = {"Name": ab}
                except:
                    data[f"Abscissa_{i}"] = np.array(ab_temp).astype(str)
                    data_attributes[f"Abscissa_{i}"] = {"Name": ab}
        
        # Adding the wrappers to the "Data" of the parent wrapper
        for i, wrp in enumerate(list_wrappers):
            data[f"Data_{i}"] = copy.copy(wrp)

        return attributes, data, data_attributes

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

