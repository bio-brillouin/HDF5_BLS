import h5py
import numpy as np
import json
import csv
import os
import pandas as pd
# import copy

# from HDF5_BLS.load_data import load_general
from HDF5_BLS.WrapperError import *
from HDF5_BLS.load_data import load_general
HDF5_BLS_Version = "1.0"


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
    filepath: str
    save: bool # A boolean to indicate if the data should be saved (True) or not (False)

    ##########################
    #     Magic methods      #
    ##########################

    def __init__(self, filepath = None): # Test made, Dev guide made
        """Initializes the wrapper

        Parameters
        ----------
        filepath : str, optional
            The filepath of the HDF5 file to load, by default None means that a temporary file is created.
        """
        # Create a temporary HDF5 file with a single group "Brillouin"
        if filepath is None:
            self.filepath = os.path.abspath(os.path.dirname(__file__)) + "/temp.h5"
            with h5py.File(self.filepath, 'w') as file:
                group = file.create_group("Brillouin")
                group.attrs["HDF5_BLS_version"] = HDF5_BLS_Version
                group.attrs["Brillouin_type"] = "Root"
            self.save = False
        else:
            if not os.path.isfile(filepath):
                with h5py.File(filepath, 'w') as file:
                    group = file.create_group("Brillouin")
                    group.attrs["Brillouin_type"] = "Root"
                    group.attrs["HDF5_BLS_version"] = HDF5_BLS_Version
            self.filepath = filepath
            self.save = False

    def __getitem__(self, key): # Test made, Dev guide made
        """Magic method to access the data of the wrapper

        Parameters
        ----------
        key : str
            The path to the data

        Returns
        -------
        numpy array or closed h5py.Group
            The data or group corresponding to the path

        Raises
        ------
        WrapperError_StructureError
            If the path does not lead to an element.    
        """
        with h5py.File(self.filepath, 'r') as file:
            if key not in file:
                raise WrapperError_StructureError(f"The path '{key}' does not exist in the file.")
            item = file[key]
            if isinstance(item, h5py.Dataset):
                return item[()]
            return item
        # It would be better to return a new wrapper with only the selected group. But in this case we need to make sure that we will not overwrite temp.h5 by mistake.

    def __add__(self, other): # Test made, Dev guide made
        """Magic method to add two wrappers together

        Parameters
        ----------
        other : Wrapper
            The wrapper to add to the current wrapper

        Returns
        -------
        Wrapper
            The wrapper resulting from the addition of the two wrappers

        Raises
        ------
        WrapperError_FileNotFound
            If one of the two wrappers leads to a temporary file. 
        WrapperError_StructureError
            If the two wrappers don't have the same version.
        WrapperError_Overwrite
            If the two wrappers share a group of same name.
        WrapperError
            If an error occured while adding the data.
        """
        # Create the new wrapper to return
        new_wrapper = Wrapper()

        # Check if any of the filepathes of the two wrappers is a temporary filepath
        if self.filepath == new_wrapper.filepath or other.filepath == new_wrapper.filepath:
            raise WrapperError_FileNotFound("Please use wrappers that are not temporary and are saved on the disk.")

        # Checking the versions of the two files
        with h5py.File(self.filepath, 'r') as file:
            version_self = file["Brillouin"].attrs["HDF5_BLS_version"]
        with h5py.File(other.filepath, 'r') as file:
            version_other = file["Brillouin"].attrs["HDF5_BLS_version"]
        if version_self != version_other:
            raise WrapperError_StructureError("The two files have different versions of the HDF5_BLS package.")
        
        # Checking the structure of the two files to verify that the two files are compatible without overwriting
        keys_self = list(self.get_structure(filepath=self.filepath)["Brillouin"].keys())
        keys_self.remove("Brillouin_type")
        keys_other = list(self.get_structure(filepath=other.filepath)["Brillouin"].keys())
        keys_other.remove("Brillouin_type")
        
        for key in keys_self:
            if key in keys_other:
                raise WrapperError_Overwrite("At least one group has the same name in the two files.")
            
        # Choosing the attributes to combine and the ones to assign to the individual groups
        attr_combine, attr_wrp1, attr_wrp2 = {}, {}, {}
        attributes_self = self.get_attributes(path="Brillouin")
        attributes_other = other.get_attributes(path="Brillouin")
        for key in attributes_self.keys():
            if key in attributes_other.keys():
                if attributes_self[key] == attributes_other[key]:
                    attr_combine[key] = attributes_self[key]
                else:
                    attr_wrp1[key] = attributes_self[key]
            else:
                attr_wrp1[key] = attributes_self[key]
        for key in attributes_other.keys():
            if key in attributes_self.keys():
                if attributes_self[key] != attributes_other[key]:
                    attr_wrp2[key] = attributes_other[key]
            else:
                attr_wrp2[key] = attributes_other[key]
        
        # Creating the new file
        try:
            # Combining the wrappers
            keys1, keys2 = [], []  
            with h5py.File(new_wrapper.filepath, 'a') as new_file:
                group = new_file["Brillouin"]
                with h5py.File(other.filepath, 'r') as file:
                    for key in file["Brillouin"].keys():
                        if isinstance(file["Brillouin"][key], h5py.Group):
                            new_file.copy(file["Brillouin"][key], group, key)
                            keys2.append(key)
                        else:
                            group.create_dataset(key, data=file[key])
                with h5py.File(self.filepath, 'r') as file:
                    for key in file["Brillouin"].keys():
                        if isinstance(file["Brillouin"][key], h5py.Group):
                            new_file.copy(file["Brillouin"][key], group, key)
                            keys1.append(key)
                        else:
                            group.create_dataset(key, data=file[key])

            # Adding common attributes to root              
            new_wrapper.set_attributes_data(attributes=attr_combine, path="Brillouin", overwrite=True)
            # Adding file-specific attributes to the each group that is added
            for key in keys1:
                new_wrapper.set_attributes_data(attributes=attr_wrp1, path=f"Brillouin/{key}", overwrite=True)
            for key in keys2:
                new_wrapper.set_attributes_data(attributes=attr_wrp2, path=f"Brillouin/{key}", overwrite=True)
                    
        except Exception as e:
            raise WrapperError(f"A problem occured when adding the data to the file '{self.filepath}'. Error message: {e}")
        
        new_wrapper.save = True
        return new_wrapper


    ##########################
    #     Main methods       # 
    ##########################

    def add_hdf5(self, filepath, parent_group = None, overwrite = False): # Test made
        """Adds an HDF5 file to the wrapper by specifying in which group the data have to be stored. Default is the "Data" group. When adding the data, the attributes of the HDF5 file are only added to the created group if they are different from the parent's attribute.

        Parameters
        ----------
        filepath : str
            The filepath of the hdf5 file to add.
        parent_group : str, optional
            The parent group where to store the data of the HDF5 file, by default the parent group is the top group "Data". The format of this group should be "Data.Data_0.Data_0_0"
        overwrite : bool, optional
            A boolean that indicates whether the data should be overwritten if it already exists, by default False
        
        Raises
        ------
        WrapperError_FileNotFound
            Raises an error if the file could not be found.
        WrapperError_StructureError
            Raises an error if the parent group does not exist in the HDF5 file.
        WrapperError_Overwrite
            Raises an error if the group already exists in the parent group.
        WrapperError
            Raises an error if the hdf5 file could not be added to the main HDF5 file.
        """
        if not os.path.isfile(filepath):
            raise WrapperError_FileNotFound(f"The file '{filepath}' does not exist.")
        
        # Extract the name of the h5 file that we want to add
        name = os.path.basename(filepath).split(".")[0]

        # Initialize parent_group and checks to avoid overwriting the data
        if parent_group is None: 
            parent_group = "Brillouin"
        else:
            with h5py.File(self.filepath, 'r') as file:
                # Check if the parent group exists
                if parent_group not in file:
                    raise WrapperError_StructureError(f"The parent group '{parent_group}' does not exist in the HDF5 file.")
                # Check if the path leads to a group, if not, we go up one level
                if not isinstance(file[parent_group], h5py._hl.group.Group):
                    parent_group = "/".join(parent_group.split("/")[:-1])
                    
        # If there are no risks of overwriting the data, we can add the data associated to the Brillouin group to the file
        
        with h5py.File(self.filepath, 'a') as file:
            group = file[parent_group]
            if name in file[parent_group].keys() and overwrite:
                self.delete_element(path = f"{parent_group}/{name}")
                new_group = group.create_group(name)
                new_group.attrs["Brillouin_type"] = "Root"
            elif name not in file[parent_group].keys():
                new_group = group.create_group(name)
                new_group.attrs["Brillouin_type"] = "Root"
            else:
                raise WrapperError_Overwrite(f"A group with the name '{name}' already exists in the parent group '{parent_group}'.")
            
            try:
                for key, value in file.attrs.items():
                    new_group.attrs[key] = value
                with h5py.File(filepath, 'r') as file_copy:
                    for key in file_copy["Brillouin"].keys():
                        if isinstance(file_copy["Brillouin"][key], h5py.Group):
                            file.copy(file_copy["Brillouin"][key], new_group, key)
                        else:
                            new_group.create_dataset(key, data=file_copy[key])
            except Exception as e:
                raise WrapperError(f"A problem occured when adding the data to the file '{self.filepath}'. Error message: {e}")
        
        self.save = True

    def add_dictionnary(self, dic, parent_group = None, name_group = None, brillouin_type = "Measure", overwrite = False): # Test made
        """Adds a data dictionnary to the wrapper. This is the preferred way to add data using the GUI.

        Parameters
        ----------
        dic : dict
            The data dictionnary. Support for the following keys:
            - "Raw_data": the raw data
            - "PSD": a power spectral density array
            - "Frequency": a frequency array associated to the power spectral density
            - "Abscissa_...": An abscissa array for the measures where the name is written after the underscore.
            Each of these keys can either be a numpy array or a dictionnary with two keys: "Name" and "Data". The "Name" key is the name that will be given to the dataset, while the "Data" key is the data itself.
            The "Abscissa_..." keys are forced to link to a dictionnary with five keys: "Name", "Data", "Unit", "Dim_start", "Dim_end". If the abscissa applies to dimension 1 for example, the "Dim_start" key should be set to 1, and the "Dim_end" to 2.
        parent_group : str, optional
            The path to the parent path, by default None
        name_group : str, optional
            The name of the data group, by default the name is "Data_i".
        brillouin_type : str, optional            
            The type of the data group, by default the type is "Measure". Other possible types are "Calibration_spectrum", "Impulse_response", ... Please refer to the documentation of the Brillouin software for more information.
        overwrite : bool, optional
            If set to True, any name in the file corresponding to an element to be added will be overwritten. Default is False
        
        Raises
        ------  
        WrapperError_StructureError
            Raises an error if the parent group does not exist in the HDF5 file.
        WrapperError_Overwrite
            Raises an error if the group already exists in the parent group.
        WrapperError_ArgumentType
            Raises an error if arguments given to the function do not match the expected type.
        WrapperError_AttributeError
            Raises an error if the keys of the dictionnary do not match the expected keys.
        """
        # If the parent group is not specified, we set it to "Brillouin", which is the top group of the file for Brillouin spectra
        if parent_group is None: parent_group = "Brillouin"
        # If the parent group is specified, we perform checks to avoid overwriting the data
        else:
            with h5py.File(self.filepath, 'r') as file:
                # Check if the parent group exists
                if parent_group not in file:
                    raise WrapperError_StructureError(f"The parent group '{parent_group}' does not exist in the HDF5 file.")
                # Check if the path leads to a group, if not, we go up one level
                if not isinstance(file[parent_group], h5py._hl.group.Group):
                    parent_group = "/".join(parent_group.split("/")[:-1])

        # If the name is not specified, we set it by default to the "Data_i"
        if name_group is None: 
            with h5py.File(self.filepath, 'a') as file:
                group = file[parent_group]
                i = 0
                while f"Data_{i}" in group.keys(): i+=1
                name_group = f"Data_{i}"
                group.create_group(name_group)
        # If the name is specified, we check if it already exists
        else:
            with h5py.File(self.filepath, 'a') as file:
                group = file[parent_group]
                if name_group in group.keys():
                    for key in dic.keys():
                        if key == "Raw_data":
                            for e in group[name_group]:
                                if group[name_group][e].attrs["Brillouin_type"] == "Raw_data":
                                    if overwrite:
                                        self.delete_element(path = f"{parent_group}/{name_group}/{e}")
                                    else:
                                        raise WrapperError_Overwrite(f"A raw data is already in the group '{name_group}' located at '{parent_group}'.")
                                    break
                        if "Name" in dic[key].keys() and dic[key]["Name"] in group[name_group].keys():
                            if overwrite:
                                self.delete_element(path = f"{parent_group}/{name_group}/{dic[key]['Name']}")
                            else:
                                raise WrapperError_Overwrite(f"A group with the name '{name_group}' already exists in the parent group '{parent_group}'.")
                else:
                    self.create_group(name_group, parent_group=parent_group)


        # Adding the data and the abscissa to the wrapper
        with h5py.File(self.filepath, 'a') as file:
            new_group = file[parent_group][name_group]
            new_group.attrs["Brillouin_type"] = brillouin_type # We add the brillouin_type here to ensure overwrite
            for key, value in dic.items():
                if type(value) is dict and key in ["Raw_data", "Other", "PSD", "Frequency", "Shift", "Shift_std", "Linewidth", "Linewidth_std"]:
                    name_dataset = value["Name"]
                    value = np.array(value["Data"])
                    dataset = new_group.create_dataset(name_dataset, data=np.array(value))
                    dataset.attrs["Brillouin_type"] = key
                elif type(value) is dict and"Abscissa_" in key:
                    assert list(value.keys()) == ["Name", "Data", "Unit", "Dim_start", "Dim_end"], WrapperError_ArgumentType("The abscissa should be a dictionnary with the keys 'Name', 'Data', 'Unit', 'Dim_start' and 'Dim_end'.")
                    name_dataset = value["Name"]
                    dataset = new_group.create_dataset(name_dataset, data=np.array(value["Data"]))
                    dataset.attrs["Brillouin_type"] = "Abscissa_" + str(value["Dim_start"]) + "_" + str(value["Dim_end"])
                    dataset.attrs["Unit"] = value["Unit"]
                elif key == "Attributes":
                    for k, v in value.items():
                        if k in new_group.attrs.keys():
                            if overwrite:
                                new_group.attrs.modify(k, v)
                            else:
                                raise WrapperError_Overwrite(f"The attribute '{k}' already exists in the group '{name_group}'.")
                        else:
                            new_group.attrs.create(k, v)
                else:
                    raise WrapperError_ArgumentType(f"The key '{key}' is not recognized.")
        
        self.save = True

    def create_group(self, name, parent_group=None, brillouin_type = "Root", overwrite=False): # Test made
        """Creates a group in the HDF5 file

        Parameters
        ----------
        name : str
            The name of the group to create
        parent_group : str, optional
            The parent group where to create the group, by default the parent group is the top group "Data". The format of this group should be "Brillouin/Data"
        brillouin_type : str, optional
            The type of the group, by default "Root". Can be "Root", "Measure", "Calibration_spectrum", "Impulse_response", "Treatment", "Metadata"
        overwrite : bool, optional
            If set to True, any name in the file corresponding to an element to be added will be overwritten. Default is False
            
        Raises
        ------
        WrapperError
            If the group already exists
        """
        # If the path is not specified, we set it to the root of the file
        if parent_group is None: parent_group = "Brillouin"

        with h5py.File(self.filepath, 'a') as file:
            if parent_group not in file:
                raise WrapperError_StructureError(f"The parent group '{parent_group}' does not exist in the HDF5 file.")
            if name in file[parent_group]:
                if not overwrite:
                    raise WrapperError_Overwrite(f"A group with the name '{name}' already exists in the parent group '{parent_group}'.")
                else:
                    self.delete_element(parent_group+"/"+name)
                    group = file[parent_group].create_group(name)
                    group.attrs.create("Brillouin_type", brillouin_type)
            else:
                group = file[parent_group].create_group(name)
                group.attrs.create("Brillouin_type", brillouin_type)
        
        self.save = True

    def delete_element(self, path = None): # Test made
        """Deletes an element from the file

        Parameters
        ----------
        path : str
            The path to the element to delete

        Raises
        ------
        WrapperError
            Raises an error if the path does not lead to an element.
        """
        # If the path is not specified, we set it to the root of the file
        if path is None: 
            paths = []
            with h5py.File(self.filepath, 'r') as file:
                for key in file["Brillouin"].keys():
                    paths.append(key)
            for path in paths:
                self.delete_element(f"Brillouin/{path}")
            with h5py.File(self.filepath, 'a') as file:
                group = file["Brillouin"]
                for attr in list(group.attrs.keys()):
                    del group.attrs[attr]
                group.attrs["Brillouin_type"] = "Root"
                group.attrs["HDF5_BLS_version"] = HDF5_BLS_Version
            return

        # Check if the path leads to an element
        with h5py.File(self.filepath, 'a') as file:
            if path not in file:
                raise WrapperError_StructureError(f"The path '{path}' does not lead to an element.")
            # If the path leads to an element, we delete it
            else:
                try:
                    del file[path]
                except Exception as e:
                    raise WrapperError(f"An error occured while deleting the element '{path}'. Error message: {e}")
        
        self.save = True

    def get_attributes(self, path=None): # Test made
        """Returns the attributes of the file

        Parameters
        ----------
        path : str, optional
            The path to the data, by default None which means the attributes are read from the root of the file (the Brillouin group).

        Returns
        -------
        attr : dict
            The attributes of the data
        """
        # If the path is not specified, we set it to the root of the file
        if path is None: path = "Brillouin"

        # We retrieve the paths of the attributes and store them in a list
        attr = {}

        # We start by opening the file and going through the given path
        with h5py.File(self.filepath, 'r') as file:
            # If the element of the path does not exist, we raise an error
            if not path in file:
                raise WrapperError_StructureError(f"The path '{path}' does not exist in the HDF5 file.")
        
            path = path.split("/")
            path_temp = path.pop(0)
            for e in file[path_temp].attrs.keys(): 
                attr[e] = file[path_temp].attrs[e]
            for e in path:
                path_temp += "/" + e
                for e in file[path_temp].attrs.keys(): 
                    attr[e] = file[path_temp].attrs[e]
        return attr

    def get_structure(self, filepath=None): # Test made
        """Returns the structure of the file

        Parameters
        ----------
        filepath : str, optional
            The filepath to the HDF5 file, by default None which means the filepath stored in the object is the one observed.

        Returns
        -------
        dict
            The structure of the file with the types of each element in the "Brillouin_type" key.

        Raises
        ------
        WrapperError_StructureError
            Raises an error if one of the elements has no 
        """
        if filepath is None: filepath = self.filepath

        def iteration(file):
            dic = {}
            for key in file.keys():
                # Skip the structure key
                if key == "Structure": continue
                try:
                    # If the key has the attribute "Brillouin_type", we add it to the dictionary
                    dic[key] = {"Brillouin_type": file[key].attrs["Brillouin_type"]}
                except:
                    # If the key does not have the attribute "Brillouin_type", we set the default group type to "Root" and dataset type to "Raw_data"
                    if isinstance(file[key], h5py.Group):
                        dic[key] = {"Brillouin_type": "Root"}
                    else:
                        dic[key] = {"Brillouin_type": "Raw_data"}
                # If the element is a group, we iterate over it
                if isinstance(file[key], h5py.Group):
                    if file[key].attrs["Brillouin_type"] != "Metadata":
                        temp = iteration(file[key])
                        if temp: dic[key].update(temp)
            else: return dic

        with h5py.File(filepath, 'r') as file:
            structure = iteration(file)
            return structure

    def save_as_hdf5(self, filepath=None, remove_old_file=True, overwrite = False): # Test made
        """Saves the data and attributes to an HDF5 file. In practice, moves the temporary hdf5 file to a new location and removes the old file if specified.
    
        Parameters
        ----------
        filepath : str, optional
            The filepath where to save the hdf5 file. Default is None, which means the file is saved in the same location as the current file.
        
        Raises
        -------
        WrapperError_Overwrite
            If the file already exists.
        WrapperError
            Raises an error if the file could not be saved
        """
        # If the filepath is the same as the current one, we do nothing
        if filepath is None or filepath == self.filepath:
            return
        
        # If the filepath is not the same as the current one, we move the current file to the new location 
        if os.path.isfile(filepath) and not overwrite:
                raise WrapperError_Overwrite(f"The file '{filepath}' already exists.")
        
        # Copy the current file to the new location and update filepath attribute
        try:
            with h5py.File(self.filepath, 'r') as src_file:
                with h5py.File(filepath, 'w') as dst_file:
                    src_file.copy('/Brillouin', dst_file)
            # Remove the old file if specified
            if remove_old_file: 
                os.remove(self.filepath)
            self.filepath = filepath
        except Exception as e:
            raise WrapperError(f"An error occured while saving the file '{self.filepath}'. Error message: {e}")
    
        self.save = False

    def set_attributes_data(self, attributes, path = None, overwrite = False): # Test made
        """Sets the attributes of the data in the HDF5 file. If the path leads to a dataset, the attributes are added to the group containing the dataset. If overwrite is False, the attributes are not overwritten if they already exist.

        Parameters
        ----------
        attributes : dict
            The attributes to be added to the HDF5 file. in the form {"MEASURE.Sample": "Water", ...}
        path : str, optional
            The path to the dataset or group in the HDF5 file, by default None leads to the top group "Brillouin"
        overwrite : bool, optional
            A parameter to indicate whether the attributes should be overwritten if they already exist or not, by default False - attributes are not overwritten.
        """
        # If the path is not specified, we set it to the root of the file
        if path is None: path = "Brillouin"

        # Updating the attributes
        with h5py.File(self.filepath, 'a') as file:
            if  path not in file: 
                raise WrapperError_StructureError(f"The path '{path}' does not lead to an element.")
            # If the path leads to a dataset, we go up one level to get a group
            if type(file[path]) is h5py._hl.dataset.Dataset:
                path = "/".join(path.split("/")[:-1])
            # We update the attributes of the metadata group taking into account the "update" parameter
            try:
                for k, v in attributes.items():
                    if k in file[path].attrs.keys():
                        if overwrite and v:
                            file[path].attrs.modify(k, v)
                    elif v:
                        file[path].attrs.create(k, v)
            except:
                raise WrapperError(f"An error occured while updating the metadata of the HDF5 file.")

        self.save = True


    ##########################
    #    Derived methods     #
    ##########################

    def add_abscissa(self, data, parent_group, name=None, unit = "AU" , dim_start = 0, dim_end = None, overwrite = False): # Test made
        """Adds abscissa as a dataset to the "parent_group" group. 
        
        Parameters
        ----------
        data : np.ndarray
            The array corresponding to the abscissa that is to be addedto the wrapper.
        parent_group : str, optional
            The parent group where to store the data of the HDF5 file, by default the parent group is the top group "Data". The format of this group should be "Brillouin/Measure".
        name : str, optional
            The name of that is given to the abscissa dataset. If the name is not specified, it is set to "Abscissa_{dim_start}_{dim_end}"
        unit: str, optional
            The unit of the abscissa array, by default AU for Arbitrary Units
        dim_start: int, optional
            The first dimension of the abscissa array, by default 0
        dim_end: int, optional
            The last dimension of the abscissa array, by default the last number of dimension of the array
        overwrite : bool, optional 
            A parameter to indicate whether the group should be overwritten if they already exist or not, by default False - attributes are not overwritten. 

        Raises
        ------
        WrapperError_StructureError
            If the parent group does not exist in the HDF5 file.
        """
        with h5py.File(self.filepath, 'r') as file:
            if parent_group not in file:
                raise WrapperError_StructureError(f"The parent group '{parent_group}' does not exist in the HDF5 file.")
        
        if dim_end is None: dim_end = len(data.shape)
        if name is None: name = f"Abscissa_{dim_start}_{dim_end}"

        dic = {"Abscissa_":{"Name": name, 
                           "Data": data, 
                           "Unit": unit, 
                           "Dim_start": dim_start, 
                           "Dim_end": dim_end}}
        
        parent_group = parent_group.split("/")
        name_group = parent_group.pop(-1)
        parent_group = "/".join(parent_group)
        
        self.add_dictionnary(dic, parent_group = parent_group, name_group = name_group, overwrite = overwrite)

    def add_frequency(self, data, parent_group=None, name=None, overwrite=False):
        """Adds a frequency array to the wrapper by creating a new group.
        
        Parameters
        ----------
        data : np.ndarray
            The frequency array to add to the wrapper.
        parent_group : str, optional
            The parent group where to store the data of the HDF5 file. The format of this group should be "Brillouin/Measure".
        name : str, optional
            The name of the frequency dataset we want to add, and as it will be displayed in the file by any HDF5 viewer. By default the name is "Frequency".
        overwrite : bool, optional 
            A parameter to indicate whether the dataset should be overwritten if a dataset with same name already exist or not, by default False - not overwritten. 
        
        Raises
        ------
        WrapperError_StructureError
            If the parent group does not exist in the HDF5 file.
        """
        with h5py.File(self.filepath, 'r') as file:
            if parent_group not in file:
                raise WrapperError_StructureError(f"The parent group '{parent_group}' does not exist in the HDF5 file.")
        
        if name is None: name = "Frequency"

        dic = {"Frequency": {"Name": name, 
                             "Data": data}}  
        
        parent_group = parent_group.split("/")
        name_group = parent_group.pop(-1)
        parent_group = "/".join(parent_group)

        self.add_dictionnary(dic, parent_group = parent_group, name_group = name_group, overwrite = overwrite)

    def add_PSD(self, data, parent_group=None, name=None, overwrite=False): # Test made
        """Adds a PSD array to the wrapper by creating a new group.
        
        Parameters
        ----------
        data : np.ndarray
            The PSD array to add to the wrapper.
        parent_group : str, optional
            The parent group where to store the data of the HDF5 file. The format of this group should be "Brillouin/Measure".
        name : str, optional
            The name of the frequency dataset we want to add, and as it will be displayed in the file by any HDF5 viewer. By default the name is "PSD".
        overwrite : bool, optional 
            A parameter to indicate whether the dataset should be overwritten if a dataset with same name already exist or not, by default False - not overwritten. 
        
        Raises
        ------
        WrapperError_StructureError
            If the parent group does not exist in the HDF5 file.
        """
        with h5py.File(self.filepath, 'r') as file:
            if parent_group not in file:
                raise WrapperError_StructureError(f"The parent group '{parent_group}' does not exist in the HDF5 file.")
        
        if name is None: name = "PSD"

        dic = {"PSD": {"Name": name, 
                       "Data": data}}  
        
        parent_group = parent_group.split("/")
        name_group = parent_group.pop(-1)
        parent_group = "/".join(parent_group)

        self.add_dictionnary(dic, parent_group = parent_group, name_group = name_group, overwrite = overwrite)

    def add_raw_data(self, data, parent_group, name=None, overwrite=False): # Test made
        """Adds a raw data array to the wrapper by creating a new group.
        
        Parameters
        ----------
        data : np.ndarray
            The raw data array to add to the wrapper.
        parent_group : str, optional
            The parent group where to store the data of the HDF5 file. The format of this group should be "Brillouin/Measure".
        name : str, optional
            The name of the frequency dataset we want to add, and as it will be displayed in the file by any HDF5 viewer. By default the name is "Raw data".
        overwrite : bool, optional 
            A parameter to indicate whether the dataset should be overwritten if a dataset with same name already exist or not, by default False - not overwritten. 
        
        Raises
        ------
        WrapperError_StructureError
            If the parent group does not exist in the HDF5 file.
        """
        with h5py.File(self.filepath, 'r') as file:
            if parent_group not in file:
                raise WrapperError_StructureError(f"The parent group '{parent_group}' does not exist in the HDF5 file.")
        
        if name is None: name = "Raw data"

        dic = {"Raw_data": {"Name": name, 
                            "Data": data}}  
        
        parent_group = parent_group.split("/")
        name_group = parent_group.pop(-1)
        parent_group = "/".join(parent_group)

        self.add_dictionnary(dic, parent_group = parent_group, name_group = name_group, overwrite = overwrite)

    def add_treated_data(self, shift, linewidth, shift_std, linewidth_std, parent_group, name_group = None, overwrite = False): # Test made
        """Adds the arrays resulting from the treatment of the PSD to the wrapper by creating a new group.
        
        Parameters
        ----------
        shift : np.ndarray
            The shift array to add to the wrapper.
        linewidth : np.ndarray
            The linewidth array to add to the wrapper.
        shift_std : np.ndarray
            The shift standard deviation array to add to the wrapper.
        linewidth_std : np.ndarray
            The linewidth standard deviation array to add to the wrapper.
        parent_group : str, optional
            The parent group where to store the data of the HDF5 file. The format of this group should be "Brillouin/Measure".
        name_group : str, optional
            The name of the group that will be created to store the treated data. By default the name is "Treat_i" with i the number of the treatment so that the name is unique.
        overwrite : bool, optional 
            A parameter to indicate whether the dataset should be overwritten if a dataset with same name already exist or not, by default False - not overwritten. 
        
        Raises
        ------
        WrapperError_StructureError
            If the parent group does not exist in the HDF5 file.
        """
        with h5py.File(self.filepath, 'r') as file:
            if parent_group not in file:
                raise WrapperError_StructureError(f"The parent group '{parent_group}' does not exist in the HDF5 file.")
            if name_group is None:
                group = file[parent_group]
                i=0
                while f"Treat_{i}" in group.keys(): i+=1

        dic = {"Shift": {"Name": "Shift", 
                         "Data": shift},
                "Linewidth": {"Name": "Linewidth",
                              "Data": linewidth},
                "Shift_std": {"Name": "Shift_std",
                              "Data": shift_std},
                "Linewidth_std": {"Name": "Linewidth_std",
                                  "Data": linewidth_std}}  
        
        self.create_group(name_group, parent_group=parent_group)

        self.add_dictionnary(dic, parent_group = parent_group, name_group = name_group, overwrite = overwrite)

    def import_file(self, filepath, parent_group=None, creator = None, parameters = None, reshape = None, overwrite = False):
        """Adds a raw data array to the wrapper from a file.
        
        Parameters
        ----------
        filepath : str
            The filepath to the raw data file to import.
        parent_group : str, optional
            The parent group where to store the data of the HDF5 file. The format of this group should be "Brillouin/Measure".
        creator : str, optional
            The structure of the file that has to be loaded. If None, a LoadError can be raised.
        parameters : dict, optional
            The parameters that are to be used to import the data correctly.  If None, a LoadError can be raised.
        reshape : tuple, optional
            The new shape of the array, by default None means that the shape is not changed
        overwrite : bool, optional 
            A parameter to indicate whether the dataset should be overwritten if a dataset with same name already exist or not, by default False - not overwritten. 
        """
        if not os.path.isfile(filepath):
            raise WrapperError_FileNotFound(f"The file '{filepath}' does not exist.")

        dic = load_general(filepath,
                            creator=creator,
                            parameters=parameters)
        
        parent_group = parent_group.split("/")
        name_group = parent_group.pop(-1)
        parent_group = "/".join(parent_group)

        if reshape is not None: 
            dic["Raw_data"]["Data"] = np.reshape(dic["Raw_data"]["Data"], reshape)
        self.add_dictionnary(dic=dic,
                             parent_group=parent_group,
                             name_group=name_group,
                             brillouin_type="Measure",
                             overwrite=overwrite)

    def import_other(self, filepath, parent_group=None, name = None, creator = None, parameters = None, reshape = None, overwrite = False):
        """Adds a raw data array to the wrapper from a file.
        
        Parameters
        ----------
        filepath : str
            The filepath to the raw data file to import.
        parent_group : str, optional
            The parent group where to store the data of the HDF5 file. The format of this group should be "Brillouin/Measure".
        name : str, optional
            The name of the dataset, by default None.
        creator : str, optional
            The structure of the file that has to be loaded. If None, a LoadError can be raised.
        parameters : dict, optional
            The parameters that are to be used to import the data correctly.  If None, a LoadError can be raised.
        reshape : tuple, optional
            The new shape of the array, by default None means that the shape is not changed
        overwrite : bool, optional 
            A parameter to indicate whether the dataset should be overwritten if a dataset with same name already exist or not, by default False - not overwritten. 
        """
        if not os.path.isfile(filepath):
            raise WrapperError_FileNotFound(f"The file '{filepath}' does not exist.")
        
        with h5py.File(self.filepath, 'r') as f:
            if name in f[parent_group].keys():
                i=0
                while f"{name}_{i}" in f[parent_group].keys(): i+=1
                name = f"{name}_{i}"
                print(i)
                i+=1
                
        dic = load_general(filepath,
                            creator=creator,
                            parameters=parameters)
        
        parent_group = parent_group.split("/")
        name_group = parent_group.pop(-1)
        parent_group = "/".join(parent_group)

        if reshape is not None: 
            dic["Raw_data"]["Data"] = np.reshape(dic["Raw_data"]["Data"], reshape)

        dic["Raw_data"]["Name"] = name
        dic_temp = {"Other": dic["Raw_data"]}
        
        self.add_dictionnary(dic=dic_temp,
                             parent_group=parent_group,
                             name_group=name_group,
                             brillouin_type="Measure",
                             overwrite=overwrite)




    def import_properties_data(self, filepath, path = None, overwrite = False): 
        """Imports properties from an excel or CSV file into a dictionary.
    
        Parameters
        ----------
        filepath : str                           
            The filepath to the csv storing the properties of the measure. This csv is based on the spreadsheet found in the "spreadsheet" folder of the repository.
        path : str
            The path to the data in the HDF5 file.
        overwrite : bool, optional
            A boolean that indicates whether the attributes should be overwritten if they already exist, by default False.
        """
        # Check if the filepath leads to a valid csv file
        if not filepath.endswith(('.csv', '.xlsx', '.xls')):
            raise WrapperError_FileNotFound(f"The file '{filepath}' is not a valid CSV file.")
        # Check if the file exists
        elif not os.path.isfile(filepath):
            raise WrapperError_FileNotFound(f"The file '{filepath}' does not exist.")

        # Extracting the attributes from the CSV file
        new_attributes = {}
        if filepath.endswith('.csv'):
            with open(filepath, mode='r', encoding='latin1') as csv_file:
                csv_reader = csv.reader(csv_file)
                for row in csv_reader:
                    if len(row[0].split(".")) > 1 and row[0].split(".")[0] in ["FILEPROP", "SPECTROMETER", "MEASURE"]:
                        new_attributes[row[0]] = row[1]
        elif filepath.endswith('.xlsx') or filepath.endswith('.xls'):
            df = pd.read_excel(filepath)
            for index, row in df.iterrows():
                if len(row[0].split(".")) > 1 and row[0].split(".")[0] in ["FILEPROP", "SPECTROMETER", "MEASURE"]:
                    new_attributes[row[0]] = row[1]
        else:
            raise WrapperError_FileNotFound(f"The file '{filepath}' is not a valid CSV or Excel file.")

        # Updating the attributes
        self.set_properties_data(properties=new_attributes, path=path, overwrite=overwrite)

    def update_property(self, name, value, path = None):
        """Updates a property of the HDF5 file given a path to the dataset or group, the name of the property and its value.
        
        Parameters
        ----------
        name : str
            The name of the property to update.
        value : str
            The value of the property to update.
        path : str, optional
            The path of the property to update. Defaults to None sets the property at the root level.
        """
        self.set_properties_data(properties={name: value}, path=path, overwrite=True)

    ##########################
    #    Terminal methods    #
    ##########################

    def print_structure(self, lvl = 0):
        """Prints the structure of the file in the console

        Parameters
        ----------
        lvl : int, optional
            The level of indentation, by default 0.
        """
        dic = self.get_structure()

        for e in dic.keys():
            if e == "Brillouin_type":
                continue
            elif type(dic[e]) is dict:
                print("|-"*lvl + e + "(" + dic[e]["Brillouin_type"] + ")")
                self.print_metadata(dic[e], lvl+1)
            else:
                print("|-"*lvl + e)
                print("|-"*(lvl+1) + str(dic[e]))
    
    def print_metadata(self, path = None):
        """Prints the metadata of a group or dataset in the console taking into account the hierarchy of the file.

        Parameters
        ----------
        lvl : int, optional
            The level of indentation, by default 0.
        """
        if path is None: path = "Brillouin"

        dic = self.get_attributes(path)

        for k, v in dic.items():
            print(k," : ", v)
    

