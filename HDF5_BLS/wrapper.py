import h5py
import numpy as np
import json
import csv
import os
import pandas as pd
import matplotlib.pyplot as plt
# import copy

# from HDF5_BLS.load_data import load_general
from HDF5_BLS.WrapperError import *
from HDF5_BLS.load_data import load_general
import HDF5_BLS.wrapper_compatibility as compat
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
    BRILLOUIN_TYPES_DATASETS = ["Abscissa", 
                                "Amplitude", 
                                "Amplitude_err", 
                                "BLT", 
                                "BLT_std", 
                                "Frequency", 
                                "Linewidth", 
                                "Linewidth_err", 
                                "Other", 
                                "PSD", 
                                "Raw_data", 
                                "Shift", 
                                "Shift_err"]
    BRILLOUIN_TYPES_GROUPS = ["Calibration_spectrum", "Impulse_response", "Measure", "Root", "Treatment"]


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
        # If no file are given, create a temporary HDF5 file with a single group "Brillouin"
        if filepath is None:
            self.filepath = os.path.abspath(os.path.dirname(__file__)) + "/temp.h5"
            with h5py.File(self.filepath, 'w') as file:
                group = file.create_group("Brillouin")
                group.attrs["HDF5_BLS_version"] = HDF5_BLS_Version
                group.attrs["Brillouin_type"] = "Root"
        # Opens the given file
        else:
            if not os.path.isfile(filepath):
                with h5py.File(filepath, 'w') as file:
                    group = file.create_group("Brillouin")
                    group.attrs["Brillouin_type"] = "Root"
                    group.attrs["HDF5_BLS_version"] = HDF5_BLS_Version
            self.filepath = filepath
            self.compatibility_changes()
        self.save = False
        self.need_for_repack = False

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
                data = item[()]
                try:
                    shape = self.get_attributes(path=key)["MEASURE.Sampling_Matrix_Size_(Nx,Ny,Nz)_()"]
                    shape = [int(i) for i in shape.split(",")] + [-1]
                    return data.reshape(shape)
                except:
                    return data
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
        """Adds an HDF5 file to the wrapper by specifying in which group the data have to be stored. Default is the "Brillouin" group. When adding the data, the attributes of the HDF5 file are only added to the created group if they are different from the parent's attribute.

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

        if self.filepath == os.path.abspath(os.path.dirname(__file__)) + "/temp.h5":
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
        only_parent = False
        # If the parent group is not specified, we set it to "Brillouin", which is the top group of the file for Brillouin spectra
        if parent_group is None: parent_group = "Brillouin"
        # If the parent group is specified, we perform checks to avoid overwriting the data
        else:
            if parent_group == name_group:
                only_parent = True

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
        elif only_parent: 
            pass
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
                    self.create_group(name_group, parent_group=parent_group, brillouin_type = "Measure")

        # Adding the data and the abscissa to the wrapper
        with h5py.File(self.filepath, 'a') as file:
            if only_parent: 
                new_group = file[parent_group]
            else:
                new_group = file[parent_group][name_group]
            if not "Brillouin_type" in new_group.attrs.keys() or overwrite: 
                new_group.attrs["Brillouin_type"] =  brillouin_type # We add the brillouin_type here to ensure overwrite
            for key, value in dic.items():
                if type(value) is dict and "Abscissa_" in key:
                    if not list(value.keys()) == ["Name", "Data", "Unit", "Dim_start", "Dim_end"]:
                        raise WrapperError_ArgumentType("The abscissa should be a dictionnary with the keys 'Name', 'Data', 'Unit', 'Dim_start' and 'Dim_end'.")
                    
                    name_dataset = value["Name"]
                    dataset = new_group.create_dataset(name_dataset, data=np.array(value["Data"]))
                    dataset.attrs["Brillouin_type"] = "Abscissa_" + str(value["Dim_start"]) + "_" + str(value["Dim_end"])
                    dataset.attrs["Unit"] = value["Unit"]
                elif type(value) is dict and key in self.BRILLOUIN_TYPES_DATASETS:
                    name_dataset = value["Name"]
                    value = np.array(value["Data"])
                    dataset = new_group.create_dataset(name_dataset, data=np.array(value))
                    dataset.attrs["Brillouin_type"] = key
                elif key == "Attributes":
                    for k, v in value.items():
                        try:
                            if k in new_group.attrs.keys():
                                if overwrite:
                                    new_group.attrs.modify(k, str(v))
                            else:
                                new_group.attrs.create(k, v)
                        except:
                            print(f"Error while adding the attribute {k} with value {v}")
                else:
                    raise WrapperError_ArgumentType(f"The key '{key}' is not recognized.")
        
        if self.filepath == os.path.abspath(os.path.dirname(__file__)) + "/temp.h5":
            self.save = True

    def add_dictionary(self, dic, parent_group, create_group = False, brillouin_type_parent_group = None, overwrite = False): # Test made
        """Adds a data dictionary to the wrapper. This is the preferred way to add data using the GUI.

        Parameters
        ----------
        dic : dict
            The data dictionary to add. The accepted keys for this dictionary are either the one given in the self.BRILLOUIN_TYPES_DATASET list, a key starting with "Abscissa" or "Attributes".
            All the element of the dictionary are also dictionnaries.
            Except for attributes, each dictionary has at least two keys: "Name" and "Data". If an abscissa is to be added, then the keys "Dim_start", "Dim_end" and "Units" need to be populated. 
            For attributes, each key is the name of the attribute, and the value is the value of the attribute, which will automatically be converted to string if it is not a string.
        parent_group : str, optional
            The path in the file where to store the dataset.
        brillouin_type_parent_group : str, optional            
            The type of the data group where the data are stored. This argument must be given if a new group is being created. If this argument is given and overwrite is set to True, then the brillouin type of the parent group will be overwritten. Otherwise, the original brillouin type of the parent group will be used.
        overwrite : bool, optional
            If set to True, any element of the file with a name corresponding to a name given in the dictionary will be overwritten. Similarly any existing argument will be overwritten and Brillouin type will be redefined. Default is False
        
        Raises
        ------  
        WrapperError_StructureError
            Raises an error if the parent group does not exist in the HDF5 file.
        WrapperError_Overwrite
            Raises an error if the group already exists in the parent group.
        WrapperError_ArgumentType
            Raises an error if arguments given to the function do not match the expected type.
        """
        def check_parent_group(parent_group):
            with h5py.File(self.filepath, 'a') as file:
                # Check if parent group is in the file
                if parent_group not in file:
                    # if not but "create_group" is True, create the group with the given Brillouin_type
                    if create_group:
                        if not type(brillouin_type_parent_group) is None and brillouin_type_parent_group in self.BRILLOUIN_TYPES_GROUPS:
                            group = file.create_group(parent_group)
                            group.attrs["Brillouin_type"] = brillouin_type_parent_group
                        else:
                            raise WrapperError_StructureError(f"A valid Brillouin type must be given when a new group has to be created")
                    # else, raise an error
                    else:
                        raise WrapperError_StructureError(f"The parent group '{parent_group}' does not exist in the HDF5 file.")

                # Check that the path leads to a group, if not, select the group above
                if not isinstance(file[parent_group], h5py._hl.group.Group):
                    parent_group = "/".join(parent_group.split("/")[:-1])
            
            return parent_group

        def retrieve_brillouin_type(brillouin_type):
            # Retrieve existing Brillouin type is none was provided
            with h5py.File(self.filepath, 'r') as file:
                group = file[parent_group]
                brillouin_type = group.attrs["Brillouin_type"]

            return brillouin_type

        def check_dictionary():
            for k in dic.keys():
                # Check that each key is a dictionary
                if type(dic[k]) is not dict:
                    raise WrapperError_ArgumentType(f"The element '{k}' is not a dictionary")
                
                # Check that each key has a valid brillouin_type
                if "Attribute" not in k and k not in self.BRILLOUIN_TYPES_DATASETS and k.split("_")[0] != "Abscissa":
                    valid_keys = [e for e in self.BRILLOUIN_TYPES_DATASETS if e.split("_")[0] != "Abscissa"]
                    raise WrapperError_ArgumentType(f"The key '{k}' does not exist. Valid keys are: {valid_keys} or 'Abscissa_i_j'")
                #Check that if the key is an abscissa, the dictionary has the correct format
                elif k.split("_")[0] == "Abscissa":
                    l = [e for e in dic[k].keys()]
                    l.sort()
                    if not l == ["Data","Dim_end","Dim_start","Name","Units"]:
                        if not l == ["Data","Dim_end","Dim_start","Name","Unit"]:
                            raise WrapperError_ArgumentType(f"The key '{k}' does not have the correct format. It should be a dictionary with the following keys: 'Data', 'Dim_end', 'Dim_start', 'Name', 'Units'")
                # Check that if the key is not an abscissa, the dictionary has the correct format
                elif "Attribute" not in k:
                    l = [e for e in dic[k].keys()]
                    l.sort()
                    assert (l == ["Data","Name"]), WrapperError_ArgumentType(f"The key '{k}' does not have the correct format. It should be a dictionary with the following keys: 'Data', 'Name'")

        def check_raw_data():
            with h5py.File(self.filepath, 'r') as file:
                group = file[parent_group]
                for elt in group:
                    elt = group[elt]
                    if elt.attrs["Brillouin_type"] == "Raw_data":
                        if "Raw_data" in dic.keys():
                            if overwrite:
                                del group[elt.name]
                            else:
                                raise WrapperError_Overwrite("You cannot add another raw data to a group with an existing raw data")

        def check_name():
            with h5py.File(self.filepath, 'r') as file:
                group = file[parent_group]
                for key in dic.keys():
                    if "Attribute" not in key and dic[key]["Name"] in group:
                        if overwrite:
                            del group[dic[key]["Name"]]
                        else:
                            raise WrapperError_Overwrite(f"The name {dic[key]["Name"]} is already used in the group {parent_group}")

        # Check that no issues come from the parent group and get the right parent group if a path to a dataset was given
        parent_group = check_parent_group(parent_group)

        # Check that the brillouin_type is correct and get the brillouin type of the group if none was given
        brillouin_type_parent_group = retrieve_brillouin_type(brillouin_type_parent_group)

        # Check that the dictionary has valid keys
        check_dictionary()

        # Check that the user is not adding another raw data to a group with an existing raw data
        check_raw_data()

        # Check that all the names given in the dictionary are free 
        check_name()

        # Add the data and the attributes to the file
        with h5py.File(self.filepath, 'a') as file:
            group = file[parent_group]
            for key, value in dic.items():
                if key in self.BRILLOUIN_TYPES_DATASETS and key != "Abscissa":
                    if key in ["Amplitude", "Amplitude_err", "BLT", "BLT_std", "Linewidth", "Linewidth_err", "Shift", "Shift_err"]:
                        if not brillouin_type_parent_group == "Treatment":
                            raise WrapperError_StructureError(f"The brillouin_type '{brillouin_type_parent_group}' should be 'Treatment' if you want to add a dataset with type '{key}'.")
                    elif key in ["Frequency", "PSD", "Raw_data"]:
                        if not brillouin_type_parent_group in ["Calibration_spectrum", "Impulse_response", "Measure"]:
                            raise WrapperError_StructureError(f"The brillouin_type '{brillouin_type_parent_group}' should be 'Calibration_spectrum', 'Impulse_response' or 'Measure' if you want to add a dataset with type '{key}'.")
                    dataset = group.create_dataset(value["Name"], data=value["Data"])
                    dataset.attrs["Brillouin_type"] = key
                elif "Attribute" in key:
                    for k, v in value.items():
                        if k in group.attrs.keys():
                            if overwrite and v:
                                group.attrs.modify(k, str(v))
                        elif v:
                            group.attrs.create(k, str(v))
                elif key.split("_")[0] == "Abscissa":
                    dataset = group.create_dataset(value["Name"], data=value["Data"])
                    dataset.attrs["Brillouin_type"] = f"Abscissa_{value['Dim_start']}_{value['Dim_end']}"
                    if "Units" in value.keys():
                        dataset.attrs["Units"] = value["Units"]
                    else:
                        dataset.attrs["Units"] = value["Unit"]
                    
    def change_brillouin_type(self, path, brillouin_type):
        """Changes the brillouin type of an element in the HDF5 file.

        Parameters
        ----------
        path : str
            The path to the element to change the brillouin type of.
        brillouin_type : str
            The new brillouin type of the element.

        Returns
        -------
        None

        Raises
        ------
        WrapperError_StructureError
            If the path is not a valid path.
        WrapperError_ArgumentType
            If the type is not valid
        """
        def check_path():
            # Check if the path is a valid path
            with h5py.File(self.filepath, 'r') as file:
                if path not in file:
                    raise WrapperError_StructureError(f"The path '{path}' does not exist in the file.")
        
        check_path()
        
        # Check if the type is valid
        if self.get_type(path) == h5py._hl.group.Group:
            if brillouin_type not in self.BRILLOUIN_TYPES_GROUPS and brillouin_type.split("_")[0] != "Abscissa":
                raise WrapperError_ArgumentType(f"The brillouin type '{brillouin_type}' is not valid.")
        else:
            if brillouin_type not in self.BRILLOUIN_TYPES_DATASETS:
                raise WrapperError_ArgumentType(f"The brillouin type '{brillouin_type}' is not valid.")
        
        # Change the brillouin type
        with h5py.File(self.filepath, 'a') as file:
            file[path].attrs["Brillouin_type"] = brillouin_type

    def change_name(self, path, name):
        """Changes the name of an element in the HDF5 file.

        Parameters
        ----------
        path : str
            The path to the element to change the name of.
        name : str
            The new name of the element.

        Raises
        ------
        WrapperError_StructureError
            If the path does not lead to an element.
        """
        with h5py.File(self.filepath, 'a') as file:
            if path not in file:
                raise WrapperError_StructureError(f"The path '{path}' does not exist in the file.")
            new_path = "/".join(path.split("/")[:-1])+"/"+name
            file[new_path] = file[path]
            del file[path]

    def close(self, delete_temp_file = False):
        """Closes the wrapper and deletes the temporary file if it exists
        """
        # If there is no need to save the wrapper, delete the temporary file (created by default when the wrapper is created)
        if not self.save or delete_temp_file:
            if self.filepath == os.path.abspath(os.path.dirname(__file__)) + "/temp.h5":
                if os.path.isfile(self.filepath):
                    os.remove(self.filepath)
            elif self.need_for_repack:
                self.repack()

        # If the wrapper has to be saved, raise an error to prevent the user from closing the wrapper without saving it
        else:
            raise WrapperError_Save(f"The wrapper has not been saved yet.")

    def combine_datasets(self, datasets, parent_group, name, overwrite = False):
        """Combines a list of elements into a unique dataset. All the datasets must have the same shape. They are added into a new dataset where the first dimension is the number of datasets, under the group "parent_group". If the dataset already exists and overwrite is set to True, it is overwritten.

        Parameters
        ----------
        datasets : list of str
            The list of paths in the file to the datasets to combine
        name : str
            The name of the new dataset
        overwrite : bool, optional
            If a dataset with the same name already exists, overwrite it, by default False
        """
        # Check if the datasets are in the file
        for dataset in datasets:
            if not self.get_type(dataset) == h5py._hl.dataset.Dataset:
                raise WrapperError_ArgumentType(f"The datasets {dataset} are not in the file.")

        # Check if the name is not already in use
        if name in self.get_children_elements(path=parent_group):
            raise WrapperError_Overwrite(f"A dataset with the name '{name}' already exists.")
        
        # Checks that the datasets have the same shape
        shapes = []
        for dataset in datasets:
            shape = self[dataset].shape
            if not shape in shapes:
                shapes.append(self[dataset].shape)
        if len(set(shapes)) > 1:
            raise WrapperError_ArgumentType(f"The datasets have different shapes.")
    
        # Create the new dataset
        tpe = self.get_type(path = datasets[0], return_Brillouin_type = True)
        new_dataset = [self[dataset][()] for dataset in datasets]
        new_dataset = np.array(new_dataset)
        dic = {tpe: {"Name": name,
                     "Data": new_dataset}}
        
        self.add_dictionary(dic, parent_group = parent_group)

    def compatibility_changes(self):
        """
        Applies changes from previous versions of the wrapper to newest versions
        """
        with h5py.File(self.filepath, "a") as f:
            # Update the Brillouin_type attribute
            f.visititems(compat.brillouin_type_update)

            # Update the HDF5_BLS_version attribute
            f["Brillouin"].attrs["HDF5_BLS_version"] = HDF5_BLS_Version

    def copy_dataset(self, path, copy_path):
        """
        Copies the dataset at the given path to the given path.

        Parameters
        ----------
        path : str
            The path to the dataset to copy.
        copy_path : str
            The path to the dataset to copy to.

        Returns
        -------
        None
        """
        with h5py.File(self.filepath, 'r') as file:
            if path not in file:
                raise WrapperError_StructureError(f"The path '{path}' does not exist in the file.")
            if copy_path not in file:
                raise WrapperError_StructureError(f"The path '{copy_path}' does not exist in the file.")
        
        with h5py.File(self.filepath, 'a') as file:
            new_name = file[path].name.split("/")[-1]
            file[copy_path].create_dataset(name = new_name, data = file[path][()])
            for e in file[path].attrs.keys():
                print(e, file[path].attrs[e])
                file[copy_path+"/"+new_name].attrs[e] = file[path].attrs[e]

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
        
        if self.filepath == os.path.abspath(os.path.dirname(__file__)) + "/temp.h5":
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
        self.need_for_repack = True

    def export_dataset(self, path, filepath):
        """
        Exports the dataset at the given path as a numpy array.

        Parameters
        ----------
        path : str
            The path to the dataset to export.
        filepath : str
            The path to the numpy array to export to.

        Returns
        -------
        None
        """
        with h5py.File(self.filepath, 'r') as file:
            np.save(filepath, file[path][()])

    def export_group(self, path, filepath):
        """
        Exports the group at the given path as a HDF5 file.

        Parameters
        ----------
        path : str
            The path to the group to export.
        filepath : str
            The path to the HDF5 file to export to.

        Returns
        -------
        None
        """
        with h5py.File(self.filepath, 'r') as file:
            with h5py.File(filepath, 'w') as new_file:
                new_file.copy(file[path], "Brillouin")
                group = new_file["Brillouin"]
                group.attrs["Brillouin_type"] = "Root"

    def export_image(self, path, filepath, simple_image = True, image_size = None, cmap = 'viridis', colorbar = False, colorbar_label = None, axis = False, xlabel = None, ylabel = None):
        """
        Exports the dataset at the given path as an image.

        Parameters
        ----------
        path : str
            The path to the dataset to export.
        filepath : str
            The path to the image to export to.
        simple_image : bool, optional
            If set to True, the image is exported as a simple image with grayscale colormap.
        image_size : tuple, optional
            The size of the image to export. If None, the size is set to the default figure size.
        cmap : str, optional
            The colormap to use for the image. Default is 'viridis'. All the available colormaps can be found here: https://matplotlib.org/stable/tutorials/colors/colormaps.html
        colorbar : bool, optional
            If set to True, a colorbar is added to the image.
        axis : boolean, optional
            If set to True, the image is displayed with an extent given by the "MEASURE.Field_Of_View_(X,Y,Z)_(um)" attribute. If set to False, the image is displayed without any extent.
            
        Returns
        -------
        None
        """
        simple_image = False
        image_size = (5,5)
        cmap = 'jet'
        colorbar = True
        axis = True
        xlabel = "x (µm)"
        ylabel = "y (µm)"

        with h5py.File(self.filepath, 'r') as file:
            data = file[path][()]

            # Reshape the element to avoid singleton dimensions
            new_shape = []
            for s in data.shape:
                if s > 1: new_shape.append(s)
            data = data.reshape(new_shape)

            if len(data.shape) == 2:
                if simple_image:
                    data = np.nan_to_num(data, nan = np.nanmin(data))
                    plt.imsave(filepath, data, cmap='gray')
                else:
                    # Set the figure size
                    if image_size is None:
                        plt.figure()
                    else:
                        plt.figure(figsize = image_size)

                    # Display the image
                    if axis is False:
                        plt.imshow(data, cmap = cmap)
                    elif axis is True:
                        extent = self.get_attributes(path = f"{path}")["MEASURE.Field_Of_View_(X,Y,Z)_(um)"]
                        extent = [float(e) for e in extent.split(",")]
                        extent = [-extent[0]/2, extent[0]/2, -extent[1]/2, extent[1]/2]
                        plt.imshow(data, cmap = cmap, extent = extent)
                    
                    # Add a label to the x and y axis
                    if not xlabel is None:
                        plt.xlabel(xlabel)
                    if not ylabel is None:
                        plt.ylabel(ylabel)

                    # Add a colorbar if needed
                    if colorbar:
                        if colorbar_label is None:
                            plt.colorbar()
                        else:
                            plt.colorbar(label = colorbar_label)

                    # Save the image
                    plt.savefig(filepath)

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

    def get_children_elements(self, path=None, Brillouin_type = None):
        """Returns the children elements of a given path. If Brillouin_type is specified, only the children elements with the given Brillouin_type are returned.

        Parameters
        ----------
        path : str, optional
            The path to the element, by default None which means the root of the file ("Brillouin" group)
        Brillouin_type : str, optional
            The type of the element, by default None which means all the elements are returned

        Returns
        -------
        list
            The list of children elements
        """
        if path is None: path = "Brillouin"

        with h5py.File(self.filepath, 'r') as file:
            if isinstance(file[path], h5py._hl.group.Group):
                children = list(file[path].keys())
            else:
                children = []
        if Brillouin_type is None:
            return list(children)
        else:
            return [e for e in children if self.get_type(path=f"{path}/{e}", return_Brillouin_type=True) == Brillouin_type]

    def get_special_groups_hierarchy(self, path = None, brillouin_type = None):
        """Get all the groups with desired brillouin type that are hierarchically above a given path.

        Parameters
        ----------
        path : str, optional
            The path to the group, by default None which means the root group is used.
        brillouin_type : str, optional
            The type of the group, by default None which means "Root" is used

        Returns
        -------
        list
            The list of all the groups with desired brillouin type that are hierarchically above a given path.
        """
        if path is None: path = "Brillouin"
        if brillouin_type is None: brillouin_type = "Root"

        # Split the path into its components
        path_split = path.split("/")
        path_temp = ""
        #Create a list of all the groups with desired brillouin type that are hierarchically above a given path
        groups = []
        while len(path_split) > 0:
            if path_temp == "": path_temp = path_split.pop(0)
            else: path_temp = f"{path_temp}/{path_split.pop(0)}"
            childs = self.get_children_elements(path_temp)
            for e in childs:
                if self.get_type(path=f"{path_temp}/{e}", return_Brillouin_type=True) == brillouin_type:
                    groups.append(f"{path_temp}/{e}")
        return groups

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

    def get_type(self, path=None, return_Brillouin_type = False):
        """Returns the type of the element

        Parameters
        ----------
        path : str, optional
            The path to the element, by default None which means the root of the file ("Brillouin" group)

        Returns
        -------
        str
            The type of the element
        """
        if path is None:
            path = "Brillouin"

        with h5py.File(self.filepath, 'r') as file:
            if return_Brillouin_type:
                return file[path].attrs["Brillouin_type"]
            else:
                return type(file[path])

    def move(self, path, new_path):
        """
        Moves an element from one path to another. If the new group does not exist, it is created.

        Parameters
        ----------
        path : str
            The path to the element to move.
        new_path : str
            The new path to move the element to.

        Raises
        ------
        WrapperError_StructureError
            If the path does not lead to an element.
        """
        with h5py.File(self.filepath, 'a') as file:
            if path not in file:
                raise WrapperError_StructureError(f"The path '{path}' does not exist in the file.")
            if new_path not in file:
                file.create_group(new_path)
            group = file[new_path]
            name_group = path.split("/")[-1]
            group.create_group(name_group)
            for key in file[path].keys():
                file[new_path][name_group].copy(file[path][key], key)
            del file[path]

    def repack(self, force_repack = False):
        """Repacks the wrapper to minimize its size.
        """
        def copy_group(file, group, new_file, new_group):
            """Copies a group from one file to another.

            Parameters
            ----------
            file : h5py.File
                The file to copy the group from.
            group : str
                The name of the group to copy.
            new_file : h5py.File
                The file to copy the group to.
            new_group : str
                The name of the group to copy to.
            """
            # Create the new group
            new_file.create_group(new_group)

            # Copy the attributes
            for key in file[group].attrs.keys():
                new_file[new_group].attrs[key] = file[group].attrs[key]

            # Copy the data
            for key in file[group].keys():
                if isinstance(file[group][key], h5py.Group):
                    copy_group(file, group+"/"+key, new_file, new_group+"/"+key)
                else:
                    dataset = new_file[new_group].create_dataset(key, data=file[group][key])
                    dataset.attrs["Brillouin_type"] = file[group][key].attrs["Brillouin_type"]
        
        if self.need_for_repack or force_repack:
            # Create a blank HDF5 file to store the data
            temporary_file = self.filepath.replace(".h5", "_temp.h5")

            # Create a new file to store the data
            with h5py.File(self.filepath, 'r') as file_old:
                # Create a new file to store the data
                with h5py.File(temporary_file, 'w') as new_file:
                    # Copy the data and attributes from the wrapper to the new file
                    for key in file_old.keys():
                        copy_group(file_old, key, new_file, key)
        
            # Delete the old file
            os.remove(self.filepath)

            # Rename the new file to the old file
            os.rename(temporary_file, self.filepath)

            # Set the need_for_repack flag to False
            self.need_for_repack = False

    def move_channel_dimension_to_last(self, path, channel_dimension=None):
        """Moves the channel dimension to the last dimension of the data to comply with the HDF5_BLS convention.

        Parameters
        ----------
        channel_dimension : int, optional
            The dimension of the channel. Default is None, which means the channel dimension is the last dimension.
        """
        # Check if the path exists
        with h5py.File(self.filepath, 'r') as file:
            if path not in file:
                raise WrapperError_StructureError(f"The path '{path}' does not exist in the file.")
        
        # Check that the path leads to a dataset
        if not self.get_type(path = path) == h5py._hl.dataset.Dataset:
            raise WrapperError_ArgumentType(f"The path '{path}' does not lead to a dataset.")

        # Extract the data
        data = self[path]

        # If nothing has to be done on the data (either no channel dimension or the channel dimension is the last dimension), return
        if channel_dimension is None or channel_dimension == data.ndim - 1:
            return 
        
        # If the channel dimension is not the last dimension, move it to the last dimension
        data = np.moveaxis(data, channel_dimension, -1)

        # Replace the dataset, starting by extracting all its attributes, deleting the dataset and creating a new one
        with h5py.File(self.filepath, 'a') as file:
            attributes = file[path].attrs
            del file[path]
            file.create_dataset(path, data=data)
            for k, v in attributes.items():
                file[path].attrs[k] = v
        
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

    def save_properties_csv(self, filepath, path = None):
        """Saves the attributes of the data in the HDF5 file to a CSV file.

        Parameters
        ----------
        filepath : str
            The filepath to the csv storing the properties of the measure. 
        path : str, optional
            The path to the data in the HDF5 file, by default None leads to the top group "Brillouin"
        """
        if path is None: 
            path = "Brillouin"
        
        attributes = self.get_attributes(path=path)
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            base = ''
            writer.writerow([attributes["HDF5_BLS_version"]])
            for k, v in attributes.items():
                if k in ["Brillouin_type", "HDF5_BLS_version"]:
                    continue
                if k.split(".")[0] != base:
                    base = k.split(".")[0]
                    writer.writerow([""])
                    writer.writerow([base])
                writer.writerow([k, v])

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

        if self.filepath == os.path.abspath(os.path.dirname(__file__)) + "/temp.h5":
            self.save = True


    ##########################
    #    Derived methods     #
    ##########################

    def add_abscissa(self, data, parent_group, name=None, unit = "AU", dim_start = 0, dim_end = None, overwrite = False): # Test made
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
        if dim_end is None: dim_end = len(data.shape)
        if name is None: name = f"Abscissa_{dim_start}_{dim_end}"

        dic = {"Abscissa_":{"Name": name, 
                           "Data": data, 
                           "Unit": unit, 
                           "Dim_start": dim_start, 
                           "Dim_end": dim_end}}
        
        self.add_dictionary(dic, 
                            parent_group = parent_group, 
                            create_group=True, 
                            brillouin_type_parent_group="Measure", 
                            overwrite = overwrite)

    def add_attributes(self, attributes, parent_group=None, overwrite=False): # Test made
        """Adds attributes to the wrapper.

        Parameters
        ----------
        attributes : dict
            The attributes to add to the wrapper. The keys of the dictionary should be the name of the attributes, and the values should be the values of the attributes.
        parent_group : str, optional
            The parent group where to store the attributes of the HDF5 file. The format of this group should be "Brillouin/Measure".
        overwrite : bool, optional
            If True, the attributes will be overwritten if they already exist.
        """
        attr = {"Attributes": attributes}

        self.add_dictionary(attr, 
                            create_group=True,
                            brillouin_type_parent_group="Root",
                            parent_group = parent_group, 
                            overwrite = overwrite)

    def add_frequency(self, data, parent_group=None, name=None, overwrite=False): # Test made
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
        if name is None: name = "Frequency"

        dic = {"Frequency": {"Name": name, 
                             "Data": data}}  
        
        self.add_dictionary(dic, 
                            parent_group = parent_group, 
                            create_group=True, 
                            brillouin_type_parent_group="Measure", 
                            overwrite = overwrite)

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
        if name is None: name = "PSD"

        dic = {"PSD": {"Name": name, 
                       "Data": data}}  
        
        self.add_dictionary(dic, 
                            parent_group = parent_group, 
                            create_group=True, 
                            brillouin_type_parent_group="Measure", 
                            overwrite = overwrite)

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
        if name is None: 
            name = "Raw data"

        dic = {"Raw_data": {"Name": name, 
                            "Data": data}}  

        self.add_dictionary(dic, 
                            parent_group = parent_group, 
                            create_group=True, 
                            brillouin_type_parent_group="Measure", 
                            overwrite = overwrite)

    def add_treated_data(self, parent_group, name_group = None, overwrite = False, **kwargs): # Test made, Dev guide made
        """Adds the arrays resulting from the treatment of the PSD to the wrapper by creating a new group.
        
        Parameters
        ----------
        parent_group : str, optional
            The parent group where to store the data of the HDF5 file. The format of this group should be "Brillouin/Measure".
        name_group : str, optional
            The name of the group that will be created to store the treated data. By default the name is "Treat_i" with i the number of the treatment so that the name is unique.
        overwrite : bool, optional 
            A parameter to indicate whether the dataset should be overwritten if a dataset with same name already exist or not, by default False - not overwritten. 
        shift: np.ndarray, optional
            The shift array to add to the wrapper.
        linewidth: np.ndarray, optional
            The linewidth array to add to the wrapper.
        amplitude: np.ndarray, optional
            The amplitude array to add to the wrapper.
        blt: np.ndarray, optional
            The Loss Tangent array to add to the wrapper.
        shift_err: np.ndarray, optional
            The shift error array to add to the wrapper.
        linewidth_err: np.ndarray, optional
            The linewidth error array to add to the wrapper.
        amplitude_err: np.ndarray, optional 
            The amplitude error array to add to the wrapper.
        blt_std: np.ndarray, optional   
            The Loss Tangent error array to add to the wrapper.
            
        Raises
        ------
        WrapperError_StructureError
            If the parent group does not exist in the HDF5 file.
        """
        dic = {}
        shift = kwargs.get("shift", None)
        if shift is not None: dic["Shift"] = {"Name": "Shift", "Data": shift}
        linewidth = kwargs.get("linewidth", None)
        if linewidth is not None: dic["Linewidth"] = {"Name": "Linewidth", "Data": linewidth}
        amplitude = kwargs.get("amplitude", None)
        if amplitude is not None: dic["Amplitude"] = {"Name": "Amplitude", "Data": amplitude}
        blt = kwargs.get("blt", None)
        if blt is not None: dic["BLT"] = {"Name": "BLT", "Data": blt}
        shift_err = kwargs.get("shift_err", None)
        if shift_err is not None: dic["Shift_err"] = {"Name": "Shift error", "Data": shift_err}
        linewidth_err = kwargs.get("linewidth_err", None)
        if linewidth_err is not None: dic["Linewidth_err"] = {"Name": "Linewidth error", "Data": linewidth_err}
        amplitude_err = kwargs.get("amplitude_err", None)
        if amplitude_err is not None: dic["Amplitude_err"] = {"Name": "Amplitude error", "Data": amplitude_err}
        blt_std = kwargs.get("blt_std", None)
        if blt_std is not None: dic["BLT_std"] = {"Name": "BLT error", "Data": blt_std}
        
        if len(dic.keys()) == 0: return

        self.add_dictionary(dic, 
                            parent_group = f"{parent_group}/{name_group}", 
                            create_group=True, 
                            brillouin_type_parent_group="Treatment", 
                            overwrite = overwrite)

    def clear_empty_attributes(self, path):
        """Deletes all the attributes that are empty at the given path.

        Parameters
        ----------
        path : str
            The path to the element to delete the attributes from.
        """
        if self.get_type(path) == h5py._hl.group.Group:
            with h5py.File(self.filepath, 'a') as file:
                for e in list(file[path].attrs.keys()):
                    if file[path].attrs[e] == "":
                        file[path].attrs.pop(e, None)
        else:
            self.clear_empty_attributes(path = "/".join(path.split("/")[:-1]))

    def import_raw_data(self, filepath, parent_group=None, name = None, creator = None, parameters = None, reshape = None, overwrite = False): # Test made
        """Adds a raw data array to the HDF5 file from a file.
        
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

        dic = load_general(filepath,
                            creator=creator,
                            parameters=parameters)

        if reshape is not None: 
            dic["Raw_data"]["Data"] = np.reshape(dic["Raw_data"]["Data"], reshape)
        
        self.add_raw_data(dic["Raw_data"]["Data"], parent_group, name = name, overwrite = overwrite)

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
                i+=1
                
        dic = load_general(filepath,
                            creator=creator,
                            parameters=parameters,
                            brillouin_type = "Other")

        if reshape is not None: 
            dic["Other"]["Data"] = np.reshape(dic["Other"]["Data"], reshape)
        dic["Other"]["Name"] = name

        self.add_dictionary(dic, parent_group = parent_group, create_group = True, brillouin_type_parent_group = "Measure", overwrite = overwrite)

    def import_properties_data(self, filepath, path = None, overwrite = False, delete_child_attributes = False): 
        """Imports properties from an excel or CSV file into a dictionary.
    
        Parameters
        ----------
        filepath : str                           
            The filepath to the csv storing the properties of the measure. This csv is based on the spreadsheet found in the "spreadsheet" folder of the repository.
        path : str
            The path to the data in the HDF5 file.
        overwrite : bool, optional
            A boolean that indicates whether the attributes should be overwritten if they already exist, by default False.
        delete_child_attributes : bool, optional
            If True, all the attributes of the children elements with same name as the ones to be updated are deleted. Default is False.
        """
        def delete_attributes(path, attributes):
            if self.get_type(path) == h5py._hl.group.Group:
                with h5py.File(self.filepath, 'a') as file:
                    for e in list(file[path].attrs.keys()):
                        if e in attributes.keys():
                            file[path].attrs.pop(e, None)
                for e in self.get_children_elements(path):
                    delete_attributes(f"{path}/{e}", attributes)

        # Check if the filepath leads to a valid csv file
        if not filepath.endswith(('.csv', '.xlsx', '.xls')):
            raise WrapperError_FileNotFound(f"The file '{filepath}' is not a valid CSV file.")
        # Check if the file exists
        elif not os.path.isfile(filepath):
            raise WrapperError_FileNotFound(f"The file '{filepath}' does not exist.")

        # If the path is not given, we set it to the root of the file
        if path is None: path = "Brillouin"

        # Extracting the attributes from the attributes file
        new_attributes = {}
        if filepath.endswith('.csv'):
            with open(filepath, mode='r', encoding='latin1') as csv_file:
                csv_reader = csv.reader(csv_file)
                for row in csv_reader:
                    if len(row[0].split(".")) > 1 and row[0].split(".")[0] in ["FILEPROP", "SPECTROMETER", "MEASURE"] and row[1] != "":
                        new_attributes[row[0]] = str(row[1])
        elif filepath.endswith('.xlsx') or filepath.endswith('.xls'):
            df = pd.read_excel(filepath, header=None)
            for index, row in df.iterrows():
                if pd.notna(row[0]):
                    if len(row[0].split(".")) > 1 and row[0].split(".")[0] in ["FILEPROP", "SPECTROMETER", "MEASURE"]:
                        if pd.notna(row[1]):
                            new_attributes[row[0]] = str(row[1])
        else:
            raise WrapperError_FileNotFound(f"The file '{filepath}' is not a valid CSV, XLSX or XLS file.")

        # Delete the attributes of the children elements with same name as the ones to be updated
        if delete_child_attributes:
            delete_attributes(path, new_attributes)

        # Updating the attributes
        self.add_dictionary({"Attributes": new_attributes}, parent_group=path, overwrite=overwrite)
        
    def update_property(self, name, value, path, apply_to_all = None):
        """Updates a property of the HDF5 file given a path to the dataset or group, the name of the property and its value.
        
        Parameters
        ----------
        name : str
            The name of the property to update.
        value : str
            The value of the property to update.
        path : str
            The path of the property to update. Defaults to None sets the property at the root level.
        """
        # If the path is not specified, we set it to the root of the file
        if path is None: path = "Brillouin"
        
        if apply_to_all is None and self.get_attributes(path)["Brillouin_type"] == "Root" and len(self.get_children_elements(path = path)) > 0:
            raise WrapperError_ArgumentType("Apply to all elements or not?")
        elif apply_to_all is not None and apply_to_all:
            if self.get_type(path = path) is h5py._hl.group.Group:
                self.add_dictionary({"Attributes": {name: value}}, parent_group=path, overwrite=True)
                for e in self.get_children_elements(path = path):
                    self.update_property(name = name, value = value, path = f"{path}/{e}", apply_to_all = apply_to_all)
            else:
                return
        elif apply_to_all is not None and not apply_to_all:
            self.add_dictionary({"Attributes": {name: value}}, parent_group=path, overwrite=True)
        else:
            self.add_dictionary({"Attributes": {name: value}}, parent_group=path, overwrite=True)

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
    

if __name__ == "__main__":
    wrp = Wrapper()
    dic = {"Raw_data": {"Name": "Wonderful measure 019", 
                        "Data": np.random.random((100, 100))},
           "PSD": {"Name": "Wonderful measure 019 - PSD", 
                    "Data": np.random.random((100, 100))},
           "Frequency": {"Name": "Frequency",
                        "Data": np.random.random((100))},
           "Abscissa_": {"Name":"Time (s)", 
                          "Data":np.linspace(0,10,100), 
                          "Units":"s",
                          "Dim_start":0, 
                          "Dim_end":1}}
    wrp.add_dictionary(dic, parent_group="Brillouin/Group1/Group2/Group3/Test", create_group = True, brillouin_type_parent_group="Calibration_spectrum", overwrite=True)


    wrp.close()

