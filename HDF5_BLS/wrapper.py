import h5py
import numpy as np
import csv
import os
from PIL import Image
import copy
import pandas as pd

from HDF5_BLS.load_data import load_general
import pandas as pd
    
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
    def __init__(self, attributes = {}, data = {}, data_attributes = {}): # Test made
        self.attributes = attributes # Dictionnary storing all the attributes
        self.data = data # Dictionnary storing all the datasets or wrapper objects, group "Data" of HDF5 file
        self.data_attributes = data_attributes # Dictionnary storing all the attributes of all the data elements

    def add_hdf5_to_wrapper(self, filepath, parent_group = None): # Test made
        """Adds an hdf5 file to the wrapper by specifying in which group the data have to be stored. Default is the "Data" group. When adding the data, the attributes of the HDF5 file are only added to the created group if they are different from the parent's attribute.

        Parameters
        ----------
        filepath : str
            The filepath of the hdf5 file to add.
        parent_group : str, optional
            The parent group where to store the data of the HDF5 file, by default the parent group is the top group "Data". The format of this group should be "Data.Data_0.Data_0_0"
        """
        # Find the position where to add the HDF5 file
        par = self.data 
        if parent_group is not None:
            loc = parent_group.split(".")
            while len(loc)>0:
                temp = loc[0]
                if not temp in par.keys():
                    par[temp] = Wrapper()
                par = par[temp].data
                loc.pop(0)
        
        # Getting the i number of Data_i where to store the file
        i = 0
        while f"Data_{i}" in par.keys(): i+=1

        # Adding the file to the wrapper
        wrp = load_hdf5_file(filepath)
        wrp.attributes["ID"] = f"Data_{i}"
        par[f"Data_{i}"] = wrp

    def add_data_dictionnary(self, dic, parent_group = None, name = None):
        """Adds a data dictionnary to the wrapper. This is the preferred way to add data using the GUI.

        Parameters
        ----------
        dic : dict
            The data dictionnary. Support for the following keys:
            - "Data": the data
            - "Attributes": the attributes of the file
            - "Abscissa_...": An abscissa array for the measures where the name is written after the underscore.
        parent_group : str, optional
            The path to the parent path, by default None
        """
        # Find the position where to add the spectrum
        par = self.data 
        if parent_group is not None:
            loc = parent_group.split("/")
            if loc[0] == "Data": loc.pop(0) 
            while len(loc)>0:
                temp = loc[0]
                if not temp in par.keys():
                    par[temp] = Wrapper()
                par = par[temp].data
                loc.pop(0)

        # Getting the i number of Data_i where to store the data
        i = 0
        while f"Data_{i}" in par.keys(): i+=1

        # Adding the data and the abscissa to the wrapper
        if name is None: name = f"Data_{i}"
        if "Data" in dic.keys(): 
            data = {"Raw_data": np.array(dic["Data"])}
            if "Power Spectral Density" in dic.keys():
                data["Power Spectral Density"] = np.array(dic["Power Spectral Density"])
            if "Frequency" in dic.keys(): 
                data["Frequency"] = np.array(dic["Frequency"])
        elif "Power Spectral Density" in dic.keys() and "Frequency" in dic.keys(): 
            data = {"Power Spectral Density": np.array(dic["Power Spectral Density"]), 
                    "Frequency": np.array(dic["Frequency"])}
        for e in dic.keys():
            if "Abscissa" in e: 
                data[e] = np.array(dic[e])
        attributes = dic["Attributes"]
        attributes["ID"] = f"Data_{i}"
        attributes["FILEPROP.Name"] = name
        par[f"Data_{i}"] = Wrapper(attributes = attributes,
                                data = data,
                                data_attributes = {})

    def add_data_group_to_wrapper(self, data, parent_group = None, name = None): # Test made
        """Adds data to the wrapper by creating a new group.

        Parameters
        ----------
        data : np.ndarray
            The data to add to the wrapper.
        parent_group : str, optional
            The parent group where to store the data of the HDF5 file, by default the parent group is the top group "Data". The format of this group should be "Data.Data_0.Data_0" or "Data/Data_0/Data_0".
        name : str, optional
            The name of the data group, by default the name is the identifier of the group "Data_i".
        """
        # Find the position where to add the spectrum
        par = self.data 
        if parent_group is not None:
            loc = parent_group.split("/")
            loc.pop(0)
            while len(loc)>0:
                temp = loc[0]
                if not temp in par.keys():
                    par[temp] = Wrapper()
                par = par[temp].data
                loc.pop(0)
        
        # Getting the i number of Data_i where to store the data
        i = 0
        while f"Data_{i}" in par.keys(): i+=1

        # Adding the data and the abscissa to the wrapper
        if name is None: name = f"Data_{i}"
        par[f"Data_{i}"] = Wrapper(attributes = {"ID": f"Data_{i}", "Name":name},
                                   data = {"Raw_data": data},
                                   data_attributes = {})
    
    def add_data_group_to_wrapper_from_filepath(self, filepath, parent_group = None):
        """Adds data to the wrapper by creating a new group, using the filepath of the data.

        Parameters
        ----------
        data : np.ndarray
            The data to add to the wrapper.
        parent_group : str, optional
            The parent group where to store the data of the HDF5 file, by default the parent group is the top group "Data". The format of this group should be "Data/Data_0/Data_0".
        name : str, optional
            The name of the data group, by default the name is the identifier of the group "Data_i".
        """
        # Find the position where to add the spectrum
        par = self.data 
        if parent_group is not None:
            loc = parent_group.split("/")
            loc.pop(0)
            while len(loc)>0:
                temp = loc[0]
                if not temp in par.keys():
                    par[temp] = Wrapper()
                par = par[temp].data
                loc.pop(0)
        
        # Getting the i number of Data_i where to store the data
        i = 0
        while f"Data_{i}" in par.keys(): i+=1

        # Adding the data and the abscissa to the wrapper
        data, attributes = load_general(filepath)
        name = os.path.basename(filepath).split(".")[0]
        attributes.update({"ID": f"Data_{i}", "FILEPROP.Name":name})
        par[f"Data_{i}"] = Wrapper(attributes = attributes,
                                   data = {"Raw_data": data},
                                   data_attributes = {"Raw_data": {"Name": "Raw_data"}})
    
    def add_data_to_group(self, data, group, name = None): # Test made
        """Adds an array to an existing data group.

        Parameters
        ----------
        data : np.ndarray
            The data to add to the wrapper.
        group : str
            The group where to store the data.
        name : str, optional
            The name of the data group, by default the name is the identifier of the group "Data_i".
        """
        # Find the position where to add the spectrum
        par = self
        loc = group.split(".")
        while len(loc)>0:
            temp = loc[0]
            par = par.data
            if not temp in par.keys():
                par[temp] = Wrapper()
            par = par[temp]
            loc.pop(0)
        
        # Checking the shape of the data
        shape = par.data[f"Raw_data"].shape
        assert data.shape == shape, WrapperError(f"The shape of the data to add to the data object ({data.shape}) is different from the shape of the raw data in the group ({shape}).")

        # Getting the i number of Data_i where to store the data
        i = 0
        while f"Raw_data_{i}" in par.data.keys(): i+=1

        # Adding the data to the wrapper
        par.data[f"Raw_data_{i}"] = data

        # Adding the attributes of the data and the abscissa to the wrapper
        if name is not None: par.data_attributes[f"Raw_data_{i}"] = {"Name": name}

    def assign_name_all_abscissa(self, abscissa): # Test made
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
        assert len(abscissa) == len(self.data["Raw_data"].shape), WrapperError("The names provided for the abscissa do not match the shape of the raw data")
        for i, e in enumerate(abscissa): 
            if not f"Abscissa_{i}" in self.data_attributes.keys(): 
                self.data_attributes[f"Abscissa_{i}"] = {}
            self.data_attributes[f"Abscissa_{i}"]["Name"] = e 
        self.attributes["MEASURE.Abscissa_Names"] = ','.join(abscissa)
        
    def assign_name_one_abscissa(self, abscissa_nb, name): # Test made
        """Adds as attributes of the abscissas and the raw data, the names of the abscissas

        Parameters
        ----------
        abscissa_nb : str
            The number of the abscissa to rename ("i" or "i-j")
        name : str
            The new name of the abscissa to rename
        """
        # Adds the names of the abscissas to the attributes of the Raw data
        if not f"Abscissa_{abscissa_nb}" in self.data_attributes.keys(): 
            self.data_attributes[f"Abscissa_{abscissa_nb}"] = {}
        self.data_attributes[f"Abscissa_{abscissa_nb}"]["Name"] = name

        # Adds the names of the abscissas to the attributes of the wrapper
        abscissa = []
        for k in range(len(self.data["Raw_data"].shape)):
            if not f"Abscissa_{k}" in self.data_attributes.keys(): 
                abscissa.append(f"Abscissa_{k}")
            else:    
                abscissa.append(self.data_attributes[f"Abscissa_{k}"]["Name"])
        self.attributes["MEASURE.Abscissa_Names"] = ','.join(abscissa)

    def clear(self):
        """Clears the wrapper

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.data.clear()
        self.data_attributes.clear()
        self.attributes.clear()

    def create_abscissa_1D_min_max(self, dimension, min, max, name = None): # Test made
        """Creates an 1D abscissa array from a minimal and maximal value

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
        assert dimension < len(self.data["Raw_data"].shape), WrapperError("The dimension provided for the abscissa is too large considering the size of the raw data")
        
        self.data[f"Abscissa_{dimension}"] = np.linspace(min, max, self.data["Raw_data"].shape[dimension])
        if not name is None:
            if not f"Abscissa_{dimension}" in self.data_attributes.keys(): 
                self.data_attributes[f"Abscissa_{dimension}"] = {}
            self.data_attributes[f"Abscissa_{dimension}"]["Name"] = name

            abscissa = []
            for k in range(len(self.data["Raw_data"].shape)):
                if not f"Abscissa_{k}" in self.data_attributes.keys(): 
                    abscissa.append(f"Abscissa_{k}")
                else:    
                    abscissa.append(self.data_attributes[f"Abscissa_{k}"]["Name"])
            self.attributes["MEASURE.Abscissa_Names"] = ','.join(abscissa)

    def export_properties_csv(self, filepath):
        """Exports the properties of the wrapper to a CSV file.

        Parameters
        ----------
        filepath : str
            The filepath to the CSV file
        """
        FILEPROP, MEASURE, SPECTROMETER = {}, {}, {}
        for k, v in self.attributes.items():
            k.replace("¬", "")
            if k.split(".")[0] == "FILEPROP":
                FILEPROP[k] = v
            elif k.split(".")[0] == "MEASURE":
                MEASURE[k] = v
            elif k.split(".")[0] == "SPECTROMETER":
                SPECTROMETER[k] = v

        with open(filepath, mode='w') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["Export"])
            csv_writer.writerow(["",""])  
            csv_writer.writerow(["FILEPROP"])    
            for k, v in FILEPROP.items():
                csv_writer.writerow([k, v])
            csv_writer.writerow(["",""])  
            csv_writer.writerow(["MEASURE"])    
            for k, v in MEASURE.items():
                csv_writer.writerow([k, v])
            csv_writer.writerow(["",""])  
            csv_writer.writerow(["SPECTROMETER"])    
            for k, v in SPECTROMETER.items():
                csv_writer.writerow([k, v])

    def get_attributes_path(self, path):
        """Returns the attributes of a path

        Parameters
        ----------
        path : str
            The path to the data

        Returns
        -------
        attr : dict
            The attributes of the data
        """
        attr = {}
        attr.update(self.attributes)
        elt = self

        if path != "Data":  # Start by retrieving the parameters of the data before modification
            path = path.split("/")[1:]
            for e in path:
                if isinstance(elt.data[e], h5py._hl.group.Group) or isinstance(elt.data[e], Wrapper):
                    elt = elt.data[e]
                    attr.update(elt.attributes)
                else:
                    if e in elt.data_attributes:
                        attr.update(elt.data_attributes[e])
                        break
        return attr
        
    def get_child(self, path):
        """Returns the wrapper corresponding to the path

        Parameters
        ----------
        path : str
            The path to the data

        Returns
        -------
        Wrapper
            The wrapper corresponding to the path
        """
        elt = self
        for e in path.split("/")[1:]:
            elt = elt.data[e]
        return elt

    def import_abscissa_1D(self, dimension, filepath, name = None): # Test made
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
        assert dimension < len(self.data["Raw_data"].shape), WrapperError("The dimension provided for the abscissa is too large considering the size of the raw data")

        self.data[f"Abscissa_{dimension}"], _ = load_general(filepath)
        if not name is None:
            if not f"Abscissa_{dimension}" in self.data_attributes.keys(): 
                self.data_attributes[f"Abscissa_{dimension}"] = {}
            self.data_attributes[f"Abscissa_{dimension}"]["Name"] = name
        
            abscissa = []
            for k in range(len(self.data["Raw_data"].shape)):
                if not f"Abscissa_{k}" in self.data_attributes.keys(): 
                    abscissa.append(f"Abscissa_{k}")
                else:    
                    abscissa.append(self.data_attributes[f"Abscissa_{k}"]["Name"])
            self.attributes["MEASURE.Abscissa_Names"] = ','.join(abscissa)
        
    def import_properties_data(self, filepath, update = False): # Test made
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
        with open(filepath, mode='r', encoding='latin1') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                if len(row[0].split("."))>1 and row[0].split(".")[0] in ["FILEPROP", "SPECTROMETER", "MEASURE"]:
                    key, value = row[0], row[1]
                    if key in self.attributes.keys():
                        if update and value:
                            self.attributes[key] = value
                    else:
                        self.attributes[key] = value
    
    def import_properties_data_attributes(self, data_key, filepath, update = False):
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
                if len(row[0].split("."))>1 and row[0].split(".")[0] in ["FILEPROP", "SPECTROMETER", "MEASURE"]:
                    key, value = row[0], row[1]
                    if key in self.attributes.keys():
                        if update and value:
                            self.data_attributes[data_key][key] = value
                    else:
                        if not data_key in self.data_attributes.keys():
                            self.data_attributes[data_key] = {}
                        self.data_attributes[data_key][key] = value
                        
    def save_as_hdf5(self,filepath=None): # Test made
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
                if isinstance(group.data[key], np.ndarray):
                    dg = data_group.create_dataset(key, data=group.data[key])
                    if key in group.data_attributes.keys():
                        for k, v in group.data_attributes[key].items():
                            dg.attrs[k] = v
                elif isinstance(group.data[key], Wrapper):
                    save_group(data_group, group.data[key], key)
                else:
                    raise WrapperError("Cannot add the selected type to HDF5 file")
                

        # try:
        if filepath is None: return
        with h5py.File(filepath, 'w') as hdf5_file:
            # Save attributes
            for key, value in self.attributes.items():
                hdf5_file.attrs[key] = value

            # Create Data group
            data_group = hdf5_file.create_group("Data")

            # Save datasets and apply the attributes
            for key in self.data.keys():
                if isinstance(self.data[key], np.ndarray):
                    dg = data_group.create_dataset(key, data=self.data[key])
                    if key in self.data_attributes.keys():
                        for k, v in self.data_attributes[key].items():
                            dg.attrs[k] = v
                elif isinstance(self.data[key], Wrapper):
                    save_group(data_group, self.data[key], key)
                else:
                    raise WrapperError("Cannot add the selected type to HDF5 file")

    def type_path(self, key):
        """Returns the path of the data type
        
        Parameters
        ----------
        key : str
            The key of the data type
            
        Returns
        -------
        str
            The type of the element
        """
        try:
            keys = key.split("/")
        except: 
            return type(self)
        keys.pop(0)
        element = self.data
        for e in keys:
            try:
                element = element[e]
            except TypeError:
                element = element.data[e]
        return type(element)

    def update_property(self, properties):
        """Updates the properties of the wrapper given the dictionnary properties

        Parameters
        ----------
        properties : dic
            The dictionnary containing the new properties to update
        """
        for k, v in properties.items():
            self.attributes[k] = v   

    def update_property_data(self, key, properties):
        """Updates the properties of the data given the dictionnary properties

        Parameters
        ----------
        properties : dic
            The dictionnary containing the new properties to update
        """
        if key in self.data_attributes.keys():
            for k, v in properties.items():
                self.data_attributes[key][k] = v
        else:
            self.data_attributes[key] = properties

def load_hdf5_file(filepath): # Test in add_hdf5_to_wrapper
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
        """Loads a group from an HDF5 file

        Parameters
        ----------
        group : HDF5 group
            The group to load

        Returns
        -------
        Wrapper
            The wrapper associated to the HDF5 group

        Raises
        ------
        WrapperError
            Raises an error if the group is not a group or a dataset
        """
        attributes, data_attributes, data = {}, {}, {}

        for k, v in group.items(): # Iterate over the group's items
            if isinstance(v, h5py._hl.dataset.Dataset): 
                data[k] = np.array(v) # If the item is a dataset, add it to the data dictionary
            elif isinstance(v, h5py._hl.group.Group):  data[k] = load_group(v) # If the item is a group, add it to the data dictionary
            else: raise WrapperError("Trying to add an object that is neither a group nor a dataset")

            data_attributes[k] = {}
            for ka, va in group[k].attrs.items():  data_attributes[k][ka] = va

        for k, v in group.attrs.items(): attributes[k] = v

        return Wrapper(attributes, data, data_attributes)
     
    attributes, data_attributes, data = {}, {}, {} 

    with h5py.File(filepath, 'r') as hdf5_file:
        for k, v in hdf5_file.attrs.items(): 
            attributes[k] = v

        for k in hdf5_file["Data"].keys():
            h5 = hdf5_file["Data"][k]

            if isinstance(h5, h5py._hl.dataset.Dataset): data[k] = h5[:]
            elif isinstance(h5, h5py._hl.group.Group): data[k] = load_group(h5)
            else: raise WrapperError("Trying to add an object that is neither a group nor a dataset")
            
            data_attributes[k] = {}
            for ka, va in h5.attrs.items(): data_attributes[k][ka] = va

    return Wrapper(attributes, data, data_attributes)

def merge_wrappers(list_wrappers, name = None, abscissa_from_attributes = None):
        """ Merges a list of wrappers into a single wrapper, combining their common attributes.

        Parameters
        ----------
        list_wrappers : list of Wrapper objects
            The list of Wrapper objects to merge into a single Wrapper object.
        name: None or str, optional
            The name given to the file resulting of the merging of the wrappers
        abscissa_from_attributes: None or list of str, optional
            The name of the attributes from which to extract values to create an abscissa
        
        Returns
        -------
        attributes : dic
            The attributes of the merged wrapper
        data : dic
            The data of the merged wrapper
        data_attributes : dic
            The attributes of the data of the merged wrapper
        """
        # Initializing the parameters of the new wrapper
        attributes = list_wrappers[0].attributes.copy()
        data, data_attributes = {}, {}

        # Extracting the common attributes by joining the attributes and deleting the attributes that are not the same for all the wrappers
        for wrp in list_wrappers[1:]:
            old_attributes = attributes.copy()
            for k,v in old_attributes.items():
                if wrp.attributes[k] != v: del attributes[k]
        
        # Creating the new abscissa from the attributes of the wrappers
        if abscissa_from_attributes is not None:
            assert type(abscissa_from_attributes) is list, WrapperError("The abscissa_from_attributes parameter should be a list of strings")
            for i, ab in enumerate(abscissa_from_attributes):
                ab_temp = [wrp.attributes[ab] for wrp in list_wrappers]

                try: data[f"Abscissa_{i}"] = np.array(ab_temp).astype(float)
                except: data[f"Abscissa_{i}"] = np.array(ab_temp).astype(str)

                data_attributes[f"Abscissa_{i}"] = {"Name": ab}
        
        # Adding the wrappers to the "Data" of the parent wrapper
        for i, wrp in enumerate(list_wrappers): data[f"Data_{i}"] = copy.copy(wrp)
        
        # Adding the name of the new wrapper
        attributes["Name"] = name

        return attributes, data, data_attributes
