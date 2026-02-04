from HDF5_BLS import Wrapper
from HDF5_BLS.errors import WrapperError_Overwrite, WrapperError_Save
from HDF5_BLS.wrapper import HDF5_group, HDF5_dataset

class HDF5Handler:
    def __init__(self, wrapper=None):
        self.wrp = wrapper if wrapper else Wrapper()
        self.filepath = None

    def new_hdf5(self):
        self.wrp = Wrapper()
        self.filepath = None

    def open_hdf5(self, filepath):
        self.filepath = filepath
        self.wrp = Wrapper(filepath)

    def save_as_hdf5(self, filepath, overwrite=False):
        self.wrp.save_as_hdf5(filepath, overwrite=overwrite)
        self.filepath = filepath

    def repack(self):
        self.wrp.repack(force_repack=True)

    def delete_element(self, path):
        self.wrp.delete_element(path=path)

    def get_children_elements(self, path="Brillouin"):
        return self.wrp.get_children_elements(path=path)

    def get_type(self, path, return_Brillouin_type=False):
        return self.wrp.get_type(path=path, return_Brillouin_type=return_Brillouin_type)

    def get_attributes(self, path):
        return self.wrp.get_attributes(path=path)

    def add_attributes(self, attributes, parent_group, overwrite=False):
        self.wrp.add_attributes(attributes=attributes, parent_group=parent_group, overwrite=overwrite)

    def create_group(self, name, parent_group, brillouin_type):
        self.wrp.create_group(name=name, parent_group=parent_group, brillouin_type=brillouin_type)

    def change_brillouin_type(self, path, brillouin_type):
        self.wrp.change_brillouin_type(path=path, brillouin_type=brillouin_type)
    
    def add_frequency(self, frequency, parent_group, name="Frequency", overwrite=False):
        self.wrp.add_frequency(data=frequency, parent_group=parent_group, name=name, overwrite=overwrite)

    def import_raw_data(self, filepath, parent_group, name="Raw data", creator=None, parameters=None, overwrite=False):
        self.wrp.import_raw_data(filepath=filepath, parent_group=parent_group, name=name, creator=creator, parameters=parameters, overwrite=overwrite)

    def import_PSD(self, filepath, parent_group, name="PSD", creator=None, parameters=None, overwrite=False):
        self.wrp.import_PSD(filepath=filepath, parent_group=parent_group, name=name, creator=creator, parameters=parameters, overwrite=overwrite)
