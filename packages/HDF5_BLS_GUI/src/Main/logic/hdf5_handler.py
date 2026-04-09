from HDF5_BLS import Wrapper
from HDF5_BLS.errors import WrapperError_Overwrite, WrapperError_Save
from HDF5_BLS.wrapper import HDF5_group, HDF5_dataset

import pyperclip

class HDF5Handler:
    def __init__(self, wrapper=None):
        self.wrp = wrapper if wrapper else Wrapper()
        self.filepath = None

    def add_attributes(self, attributes, parent_group, overwrite=False):
        self.wrp.add_attributes(attributes=attributes, parent_group=parent_group, overwrite=overwrite)

    def add_frequency(self, frequency, parent_group, name="Frequency", overwrite=False):
        self.wrp.add_frequency(data=frequency, parent_group=parent_group, name=name, overwrite=overwrite)

    def add_hdf5(self, filepath, parent_group):
        self.wrp.add_hdf5(filepath = filepath, parent_group = parent_group, overwrite = False)

    def change_brillouin_type(self, path, brillouin_type):
        self.wrp.change_brillouin_type(path=path, brillouin_type=brillouin_type)
    
    def change_name(self, path, name):
        self.wrp.change_name(path=path, name=name)
    
    def create_group(self, name, parent_group):
        self.wrp.create_group(name=name, parent_group=parent_group, brillouin_type="Root")

    def delete_element(self, path):
        self.wrp.delete_element(path=path)

    def export_path_clipboard(self, path):
        """Copy the path of the selected element to the clipboard.
        """ 
        pyperclip.copy(path)

    def export_group(self, path, filepath):
        """Export the group to an HDF5 file.
        """
        self.wrp.export_group(path, filepath)

    def get_children_elements(self, path="Brillouin"):
        return self.wrp.get_children_elements(path=path)

    def get_type(self, path, return_Brillouin_type=False):
        return self.wrp.get_type(path=path, return_Brillouin_type=return_Brillouin_type)

    def get_attributes(self, path):
        return self.wrp.get_attributes(path=path)

    def import_PSD(self, filepath, parent_group, name="PSD", creator=None, parameters=None, overwrite=False, create_group = True):
        name = filepath.split("/")[-1].split(".")[0]
        if create_group:
            self.wrp.create_group(name = name, 
                                    parent_group = parent_group, 
                                    brillouin_type = "Measure", 
                                overwrite=False)
            self.wrp.import_PSD(filepath=filepath, parent_group=f"{parent_group}/{name}", name='PSD', creator=creator, parameters=parameters, overwrite=overwrite)
        else:
            self.wrp.import_PSD(filepath=filepath, parent_group=parent_group, name='PSD', creator=creator, parameters=parameters, overwrite=overwrite)
    def import_raw_data(self, filepath, parent_group, name="Raw data", creator=None, parameters=None, overwrite=False):
        try:
            parent_type = self.get_type(parent_group, return_Brillouin_type=True)
        except:
            parent_type = "Root"

        if parent_type == "Measure":
            has_raw_or_psd = False
            for child in self.get_children_elements(parent_group):
                child_type = self.get_type(f"{parent_group}/{child}", return_Brillouin_type=True)
                if child_type in ["Raw_data", "PSD"]:
                    has_raw_or_psd = True
                    break
            
            if has_raw_or_psd:
                new_name = filepath.split("/")[-1].split(".")[0]
                self.wrp.import_other(filepath=filepath, parent_group=parent_group, name=new_name, creator=creator, parameters=parameters, overwrite=overwrite)
            else:
                if creator == 'GHOST':
                    self.import_PSD(filepath=filepath, parent_group=parent_group, name='PSD', creator=creator, parameters=parameters, overwrite=overwrite, create_group=False)
                else:
                    self.wrp.import_raw_data(filepath=filepath, parent_group=parent_group, name='Raw data', creator=creator, parameters=parameters, overwrite=overwrite)
            return

        if creator == 'GHOST':
            self.import_PSD(filepath=filepath, parent_group=parent_group, name='PSD', creator=creator, parameters=parameters, overwrite=overwrite, create_group=True)
        else:
            name = filepath.split("/")[-1].split(".")[0]
            self.wrp.create_group(name = name, 
                                    parent_group=parent_group, 
                                    brillouin_type = "Measure", 
                                    overwrite=overwrite)
            self.wrp.import_raw_data(filepath=filepath, parent_group=f"{parent_group}/{name}", name='Raw data', creator=creator, parameters=parameters, overwrite=overwrite)

    def move_element(self, path, new_parent):
        self.wrp.move(path=path, new_path=new_parent)

    def new_hdf5(self):
        self.wrp = Wrapper()
        self.filepath = None

    def open_hdf5(self, filepath):
        self.filepath = filepath
        self.wrp = Wrapper(filepath)

    def repack(self):
        self.wrp.repack(force_repack=True)

    def save_as_hdf5(self, filepath, overwrite=False):
        self.wrp.save_as_hdf5(filepath, overwrite=overwrite)
        self.filepath = filepath
