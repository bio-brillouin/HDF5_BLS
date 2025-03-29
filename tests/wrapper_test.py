import h5py
import os
import inspect
import numpy as np
import sys
import numpy as np

directory = os.path.dirname(os.path.realpath(__file__)).split("/")[:-1]
directory = "/".join(directory)
sys.path.insert(0, directory)
from HDF5_BLS.wrapper import Wrapper, HDF5_BLS_Version
from HDF5_BLS.WrapperError import *


def test_init():
    # Initialize the wrapper
    directory=os.path.dirname(os.path.abspath(__file__))
    w = Wrapper()
    # Check if "temp.h5" exists in the folder containing the wrapper_v2 package
    wrapper_v2_path = os.path.dirname(inspect.getfile(Wrapper))
    temp_file_path = os.path.join(wrapper_v2_path, "temp.h5")
    assert os.path.isfile(temp_file_path), f"temp.h5 not found in {wrapper_v2_path}"
    # Remove the temporary file
    os.remove(temp_file_path)
    # Create a new wrapper by specifying the path of the file
    w = Wrapper(filepath = directory+"/test_1.h5")
    assert os.path.isfile(directory+"/test_1.h5"), f"test_1.h5 not found in {directory}"
    with h5py.File(w.filepath, 'r') as file:
        assert list(file.keys()) == ["Brillouin"], f"At initialization the file does not match the initial structure" # Check that only one group exists at initialization
        assert file["Brillouin"].attrs["Brillouin_type"] == "Root", f"At initialization the root group does not have the right Brillouin_type" # Check that the group is of type "Root"
        assert file["Brillouin"].attrs["HDF5_BLS_version"] == HDF5_BLS_Version, f"At initialization the root group does not have the right HDF5_BLS_version" # Check that the group is of type "Root"
    os.remove(directory+"/test_1.h5")

def test_get_item_():
    # Initialize the wrapper
    directory=os.path.dirname(os.path.abspath(__file__))
    w = Wrapper(directory+"/test.h5")
    # Check that we can access the Brillouin group correctly
    assert isinstance(w["Brillouin"], h5py.Group), f"The access of the file with the magic method _get_item_ failed" # Check that the group is of type "Root"
    # Remove the temporary file
    os.remove(directory+"/test.h5")

def test_add_():
    # Creating the first file
    directory=os.path.dirname(os.path.abspath(__file__))
    w1 = Wrapper(filepath=directory+"/file1.h5")
    dic = {"Raw_data": {"Name": "Measure_1",
                        "Data": np.random.random((50,50,100))}}
    w1.add_dictionnary(dic, parent_group="Brillouin", name_group="Group1")
    # Create the second file as a temporary file and verify that we get a WrapperError_FileNotFound
    w2 = Wrapper()
    dic = {"Raw_data": {"Name": "Measure_2",
                        "Data": np.random.random((50,50,100))}}
    w2.add_dictionnary(dic, parent_group="Brillouin", name_group="Group2")
    try: w = w1 + w2
    except WrapperError_FileNotFound: pass
    # Create the second file and force a wrong version of the HDF5 file to check if we get a WrapperError_StructureError
    w2 = Wrapper(filepath = directory+"/file2.h5")
    w2.set_attributes_data(attributes={"HDF5_BLS_version": "0.1"}, path="Brillouin", overwrite=True)
    dic = {"Raw_data": {"Name": "Measure_2",
                        "Data": np.random.random((50,50,100))}}
    w2.add_dictionnary(dic, parent_group="Brillouin", name_group="Group2")
    try: w = w1 + w2
    except WrapperError_StructureError: pass
    os.remove(w2.filepath)
    # Create the second file with a group of same name than in the first file
    w2 = Wrapper(filepath = directory+"/file2.h5")
    dic = {"Raw_data": {"Name": "Measure_2",
                        "Data": np.random.random((50,50,100))}}
    w2.add_dictionnary(dic, parent_group="Brillouin", name_group="Group1")
    try: w = w1 + w2
    except WrapperError_Overwrite: pass
    os.remove(w2.filepath)
    # Create a second file with everythin OK for the addition and check that the data is added correctly, including the attributes
    w2 = Wrapper(filepath = directory+"/file2.h5")
    dic = {"Raw_data": {"Name": "Measure_2",
                        "Data": np.random.random((50,50,100))}}
    w2.add_dictionnary(dic, parent_group="Brillouin", name_group="Group2")
    attr1 = {"Common_attribute": "42", "Different_attribute": "12"}
    attr2 = {"Common_attribute": "42", "Different_attribute": "24"}
    w1.set_attributes_data(attributes=attr1, path="Brillouin", overwrite=True)
    w2.set_attributes_data(attributes=attr2, path="Brillouin", overwrite=True)
    w = w1 + w2
    with h5py.File(w.filepath, 'r') as file:
        assert "Group1" in file["Brillouin"], f"The group 'Group1' does not exist in the file"
        assert "Group2" in file["Brillouin"], f"The group 'Group1' does not exist in the file"
        assert "Measure_1" in file["Brillouin/Group1"], f"The dataset 'Measure_1' is not in the file"
        assert "Measure_2" in file["Brillouin/Group2"], f"The dataset 'Measure_2' is not in the file"
        assert w.get_attributes(path="Brillouin/Group1")["Common_attribute"] == "42", f"The attribute 'Common_attribute' is not OK"
        assert w.get_attributes(path="Brillouin/Group2")["Common_attribute"] == "42", f"The attribute 'Common_attribute' is not OK"
        assert w.get_attributes(path="Brillouin/Group1")["Different_attribute"] == "12", f"The attribute 'Different_attribute' is not OK"
        assert w.get_attributes(path="Brillouin/Group2")["Different_attribute"] == "24", f"The attribute 'Different_attribute' is not OK"
    # Removing temporary files
    os.remove(w.filepath)
    os.remove(w1.filepath)
    os.remove(w2.filepath)
    
def test_add_hdf5():
    directory=os.path.dirname(os.path.abspath(__file__))
    w = Wrapper()
    # Trying to add a file that does not exist
    try: w.add_hdf5(filepath = "Wrong_path", parent_group="Brillouin", overwrite=True), f"The add_hdf5 method failed"
    except WrapperError_FileNotFound: pass 
    # Creating a temporary file
    w1 = Wrapper(filepath=directory+"/test_1.h5")
    dic = {"Raw_data": {"Name": "Measure_1",
                        "Data": np.random.random((50,50,100))}}
    w1.add_dictionnary(dic, parent_group="Brillouin", name_group="Group1")
    # Adding the new file to the original wrapper without parent group
    w.add_hdf5(filepath = w1.filepath)
    with h5py.File(w.filepath, 'r') as file:
        assert "test_1" in file["Brillouin"], f"The group storing the added file does not exist in the file"
        assert "Group1" in file["Brillouin/test_1"], f"The group 'Group1' does not exist in the file"
        assert "Measure_1" in file["Brillouin/test_1/Group1"], f"The dataset 'Measure_1' does not exist in the file"
    # Adding the new file to the original wrapper with parent group
    try: w.add_hdf5(filepath = w1.filepath, parent_group="Brillouin/Group")    
    except WrapperError_StructureError: pass
    w.create_group("Group")
    w.add_hdf5(filepath = w1.filepath, parent_group="Brillouin/Group")  
    with h5py.File(w.filepath, 'r') as file:
        assert "Group" in file["Brillouin"], f"The group storing the added file does not exist in the file"
        assert "test_1" in file["Brillouin/Group"], f"The group storing the added file does not exist in the file"
        assert "Group1" in file["Brillouin/Group/test_1"], f"The group 'Group1' does not exist in the file"
        assert "Measure_1" in file["Brillouin/Group/test_1/Group1"], f"The dataset 'Measure_1' does not exist in the file"
    # Adding the new file to a group already contining a group of same name
    try: w.add_hdf5(filepath = w1.filepath, parent_group="Brillouin/Group")  
    except WrapperError_Overwrite: pass
    # Removing temporary file
    os.remove(w1.filepath)
    os.remove(w.filepath)

def test_add_dictionnary():
    directory = os.path.dirname(os.path.realpath(__file__))
    w = Wrapper(filepath=directory+"/test_1.h5")
    dic = {"Raw_data": {"Name": "Measure Water raw",
                        "Data": np.random.random((50,50,100))},
           "PSD": {"Name": "Measure Water PSD",
                        "Data": np.random.random((50,50,100))},
           "Frequency": {"Name": "Frequency",
                        "Data": np.random.random((50,50,100))},
           "Abscissa_x": {"Name":"x", 
                          "Data":np.linspace(0,10,50), 
                          "Unit":"um",
                          "Dim_start":0, 
                          "Dim_end":1},
           "Abscissa_y": {"Name":"y", 
                          "Data":np.linspace(0,10,50), 
                          "Unit":"um",
                          "Dim_start":0, 
                          "Dim_end":1}}
    # Testing adding data without specifying anything
    w.add_dictionnary(dic)
    with h5py.File(directory+"/test_1.h5", 'r') as file:
        assert "Data_0" in list(file["Brillouin"].keys()), f"The group 'Data_0' does not exist in the file"
        assert file["Brillouin"]["Data_0"].attrs["Brillouin_type"] == "Measure", f"The group 'Data_0' does not have the right Brillouin_type"
        assert file["Brillouin"]["Data_0"]["Measure Water raw"].shape == (50,50,100), f"The dataset 'Raw_data' does not have the right shape"
    # Testing adding data to a parent group that doesn't exist
    try: w.add_dictionnary(dic, parent_group="Wrong_group")
    except WrapperError_StructureError:pass
    # Testing adding data without specifying the group
    w.add_dictionnary(dic, parent_group="Brillouin")
    with h5py.File(directory+"/test_1.h5", 'r') as file:
        assert "Data_1" in list(file["Brillouin"].keys()), f"The group 'Data_0' does not exist in the file"
        assert file["Brillouin"]["Data_1"].attrs["Brillouin_type"] == "Measure", f"The group 'Data_0' does not have the right Brillouin_type"
        assert file["Brillouin"]["Data_1"]["Measure Water raw"].shape == (50,50,100), f"The dataset 'Raw_data' does not have the right shape"
    # Testing adding data by creating a new group and specifying its name
    w.add_dictionnary(dic, parent_group="Brillouin", name_group="Test")
    with h5py.File(directory+"/test_1.h5", 'r') as file:
        assert "Test" in list(file["Brillouin"].keys()), f"The group 'Test' does not exist in the file"
        assert file["Brillouin"]["Test"].attrs["Brillouin_type"] == "Measure", f"The group 'Test' does not have the right Brillouin_type"
        assert file["Brillouin"]["Test"]["Measure Water raw"].shape == (50,50,100), f"The dataset 'Raw_data' does not have the right shape"
    # Testing adding data to a calibration group
    dic2 = {"PSD": {"Name": "Measure Water PSD",
                        "Data": np.random.random((50,50,100))},
           "Frequency": {"Name": "Frequency",
                        "Data": np.random.random((50,50,100))}}
    w.add_dictionnary(dic2, parent_group="Brillouin", name_group="Calibration", brillouin_type="Calibration_spectrum")
    with h5py.File(directory+"/test_1.h5", 'r') as file:
        assert "Calibration" in list(file["Brillouin"].keys()), f"The group 'Test' does not exist in the file"
        assert file["Brillouin"]["Calibration"].attrs["Brillouin_type"] == "Calibration_spectrum", f"The group 'Test' does not have the right Brillouin_type"
        assert file["Brillouin"]["Test"]["Measure Water PSD"].shape == (50,50,100), f"The dataset 'Raw_data' does not have the right shape"
    # Testing adding another Raw data to a group already containing Raw data
    dic = {"Raw_data": {"Name": "Measure Water raw",
                        "Data": np.random.random((50,50,100))}}
    try: w.add_dictionnary(dic, parent_group="Brillouin", name_group="Test")
    except WrapperError_Overwrite: pass
    # Testing adding a dataset with the same name
    dic = {"Frequency": {"Name": "Measure Water PSD",
                        "Data": np.random.random((50,50,100))}}
    try: w.add_dictionnary(dic, parent_group="Brillouin", name_group="Test")
    except WrapperError_Overwrite: pass
    # Testing overwriting a dataset with the same name
    dic = {"Frequency": {"Name": "Measure Water raw",
                        "Data": np.random.random((50,100))}}
    w.add_dictionnary(dic, parent_group="Brillouin", name_group="Test", overwrite=True)
    with h5py.File(directory+"/test_1.h5", 'r') as file:
        assert file["Brillouin"]["Test"]["Measure Water raw"].shape == (50,100), f"The dataset 'Raw_data' does not have the right shape"
    # Removing temporary file
    os.remove(directory+"/test_1.h5")

def test_add_abscissa():
    # Initialize the wrapper
    directory = os.path.dirname(os.path.realpath(__file__))
    w = Wrapper(filepath=directory+"/test_1.h5")
    abscissa = np.linspace(0, 10, 100)
    # Check that the function fails if the parent group does not exist
    try: w.add_abscissa(data=abscissa, parent_group="Brillouin/Test")
    except WrapperError_StructureError: pass
    # Create the group and add the abscissa to it and check that the data is added correctly
    w.create_group("Test", parent_group="Brillouin")
    w.add_abscissa(data=abscissa, parent_group="Brillouin/Test", name="x", unit = "mm" , dim_start = 0, dim_end = 1, overwrite = False)
    with h5py.File(directory+"/test_1.h5", 'r') as file:
        assert "x" in file["Brillouin"]["Test"], f"The dataset 'x' does not exist"
        assert file["Brillouin"]["Test"]["x"].shape == (100,), f"The dataset 'x' does not have the right shape"
        assert file["Brillouin"]["Test"]["x"].attrs["Unit"] == "mm", f"The dataset 'x' does not have the right unit"
        assert file["Brillouin"]["Test"]["x"].attrs["Brillouin_type"] == "Abscissa_0_1", f"The dataset 'x' does not have the right Dim_start"
    # Removing temporary file
    os.remove(directory+"/test_1.h5")

def test_add_raw_data():
    # Initialize the wrapper
    directory = os.path.dirname(os.path.realpath(__file__))
    w = Wrapper(filepath=directory+"/test_1.h5")
    data = np.random.rand(100, 100)
    # Check that the function fails if the parent group does not exist
    try: w.add_raw_data(data=data, parent_group="Brillouin/Test")
    except WrapperError_StructureError: pass
    # Create the group and add the raw data to it and check that the data is added correctly
    w.create_group("Test", parent_group="Brillouin")
    w.add_raw_data(data=data, parent_group="Brillouin/Test", name="data", overwrite = False)
    with h5py.File(directory+"/test_1.h5", 'r') as file:
        assert "data" in file["Brillouin"]["Test"], f"The dataset 'data' does not exist"
        assert file["Brillouin"]["Test"]["data"].shape == (100, 100), f"The dataset 'data' does not have the right shape"
    # Delete the temporary file
    os.remove(directory+"/test_1.h5")

def test_add_PSD():
    # Initialize the wrapper
    directory = os.path.dirname(os.path.realpath(__file__))
    w = Wrapper(filepath=directory+"/test_1.h5")
    data = np.random.rand(100, 100)
    # Check that the function fails if the parent group does not exist
    try: w.add_PSD(data=data, parent_group="Brillouin/Test")
    except WrapperError_StructureError: pass
    # Create the group and add the raw data to it and check that the data is added correctly
    w.create_group("Test", parent_group="Brillouin")
    w.add_PSD(data=data, parent_group="Brillouin/Test", name="PSD", overwrite = False)
    with h5py.File(directory+"/test_1.h5", 'r') as file:
        assert "PSD" in file["Brillouin"]["Test"], f"The dataset 'data' does not exist"
        assert file["Brillouin"]["Test"]["PSD"].shape == (100, 100), f"The dataset 'data' does not have the right shape"
    # Delete the temporary file
    os.remove(directory+"/test_1.h5")

def test_add_frequency():
    # Initialize the wrapper
    directory = os.path.dirname(os.path.realpath(__file__))
    w = Wrapper(filepath=directory+"/test_1.h5")
    data = np.random.rand(100, 100)
    # Check that the function fails if the parent group does not exist
    try: w.add_frequency(data=data, parent_group="Brillouin/Test")
    except WrapperError_StructureError: pass
    # Create the group and add the raw data to it and check that the data is added correctly
    w.create_group("Test", parent_group="Brillouin")
    w.add_frequency(data=data, parent_group="Brillouin/Test", name="Freq", overwrite = False)
    with h5py.File(directory+"/test_1.h5", 'r') as file:
        assert "Freq" in file["Brillouin"]["Test"], f"The dataset 'data' does not exist"
        assert file["Brillouin"]["Test"]["Freq"].shape == (100, 100), f"The dataset 'data' does not have the right shape"
    # Delete the temporary file
    os.remove(directory+"/test_1.h5")

def test_add_treated_data():
    # Initialize the wrapper
    directory = os.path.dirname(os.path.realpath(__file__))
    w = Wrapper(filepath=directory+"/test_1.h5")
    shift = np.random.rand(100)
    linewidth = np.random.rand(100)
    shift_std = np.random.rand(100)
    linewidth_std = np.random.rand(100)
    # Check that the function fails if the parent group does not exist
    try: w.add_treated_data(shift=shift, linewidth=linewidth, shift_std=shift_std, linewidth_std=linewidth_std, parent_group="Brillouin/Test")
    except WrapperError_StructureError: pass
    # Create the group and add the raw data to it and check that the data is added correctly    
    w.create_group("Test", parent_group="Brillouin")
    w.add_treated_data(shift=shift, linewidth=linewidth, shift_std=shift_std, linewidth_std=linewidth_std, parent_group="Brillouin/Test", name_group="Treatment")
    with h5py.File(directory+"/test_1.h5", 'r') as file:
        assert "Treatment" in file["Brillouin/Test"], f"The group 'Treatment' does not exist in the file"
        assert "Shift" in file["Brillouin/Test/Treatment"], f"The dataset 'Shift' does not exist in the file"
        assert "Linewidth" in file["Brillouin/Test/Treatment"], f"The dataset 'Linewidth' does not exist in the file"
        assert "Shift_std" in file["Brillouin/Test/Treatment"], f"The dataset 'Shift_std' does not exist in the file"
        assert "Linewidth_std" in file["Brillouin/Test/Treatment"], f"The dataset 'Linewidth_std' does not exist in the file"
    # Delete the temporary file    
    os.remove(directory+"/test_1.h5")

def test_create_group():
    # Creates an initial wrapper object and creates a group in the Brillouin group
    directory = os.path.dirname(os.path.realpath(__file__))
    w = Wrapper(filepath=directory+"/test_1.h5")
    w.create_group("Test", parent_group="Brillouin")
    # Check that providing a wrong parent group raises an error
    try: w.create_group("Test", parent_group="Wrong_Group")
    except WrapperError_StructureError: pass
    # Check that providing a group that already exists raises an error
    try: w.create_group("Test", parent_group="Brillouin")
    except WrapperError_Overwrite: pass
    os.remove(directory+"/test_1.h5")

def test_delete_element():
    # Creates an initial wrapper object and creates a group in the Brillouin group with mock data
    directory = os.path.dirname(os.path.realpath(__file__))
    w = Wrapper(filepath=directory+"/test_1.h5")
    dic = {"Raw_data": {"Name": "Measure Water raw",
                        "Data": np.random.random((50,50,100))},
           "PSD": {"Name": "Measure Water PSD",
                        "Data": np.random.random((50,50,100))},
           "Frequency": {"Name": "Frequency",
                        "Data": np.random.random((50,50,100))},
           "Abscissa_x": {"Name":"x", 
                          "Data":np.linspace(0,10,50), 
                          "Unit":"um",
                          "Dim_start":0, 
                          "Dim_end":1},
           "Abscissa_y": {"Name":"y", 
                          "Data":np.linspace(0,10,50), 
                          "Unit":"um",
                          "Dim_start":0, 
                          "Dim_end":1}}
    w.add_dictionnary(dic, parent_group="Brillouin", name_group="Test", brillouin_type="Measure")
    # Verify that if the path does not lead to an element, the function raises an error
    try: w.delete_element("Brillouin/Test/Test_0")
    except WrapperError_StructureError: pass
    # Verify that if the path leads to an element, the element is deleted but the rest of the group is not
    w.delete_element("Brillouin/Test/Measure Water raw")
    with h5py.File(directory+"/test_1.h5", 'r') as file:
        assert "Test" in file["Brillouin"], f"The group 'Test' still exists in the file"
        assert "Measure Water raw" not in file["Brillouin/Test"], f"The dataset 'Measure Water raw' still exists in the file"
        assert "Measure Water PSD" in file["Brillouin/Test"], f"The dataset 'PSD' doesn't exists in the file"
        assert "Frequency" in file["Brillouin/Test"], f"The dataset 'Frequency' still exists in the file"
        assert "x" in file["Brillouin/Test"], f"The dataset 'Abscissa_x' still exists in the file" 
        assert "y" in file["Brillouin/Test"], f"The dataset 'Abscissa_y' still exists in the file"
    # Verify that if the path is not given, the file contains a single group "Brillouin" that is empty  
    w.delete_element()
    with h5py.File(directory+"/test_1.h5", 'r') as file: 
        assert "Brillouin" in file, f"The dataset 'Measure Water raw' still exists in the file"
        assert len(file["Brillouin"]) == 0, f"The dataset 'Measure Water raw' still exists in the file"
    os.remove(directory+"/test_1.h5")


def test_get_attributes():
    # Initialize the wrapper
    directory = os.path.dirname(os.path.realpath(__file__))
    w = Wrapper(filepath=directory+"/test_1.h5")
    dic = {"Raw_data": {"Name": "Measure",
                        "Data": np.random.random((50,50,100))}}
    w.create_group("Test", parent_group="Brillouin")
    w.add_dictionnary(dic=dic, parent_group="Brillouin/Test", name_group = "Test_0")
    attributes_0 = {"MEASURE.Sample": "Water",
                    "SPECTROMETER.Type": "TFP"}
    w.set_attributes_data(attributes=attributes_0, path="Brillouin/Test")
    attributes_0 = {"MEASURE.Sample": "Ethanol"}
    w.set_attributes_data(attributes=attributes_0, path="Brillouin/Test/Test_0")
    attr = w.get_attributes(path="Brillouin/Test/Test_0")
    assert attr["MEASURE.Sample"] == "Ethanol", f"The attribute 'MEASURE.Sample' does not have the right value"
    assert attr["SPECTROMETER.Type"] == "TFP", f"The attribute 'SPECTROMETER.Type' does not have the right value"
    try: w.get_attributes(path="Brillouin/Wrong_path")
    except WrapperError_StructureError: pass
    os.remove(directory+"/test_1.h5")

def test_get_structure():
    directory = os.path.dirname(os.path.realpath(__file__))
    w = Wrapper(filepath=directory+"/test_1.h5")
    dic = {"Raw_data": np.random.random((50,50,100))}
    w.create_group("Test", parent_group="Brillouin")
    w.add_dictionnary(dic=dic, parent_group="Brillouin/Test", name_group = "Test_0")
    struct = w.get_structure()
    assert list(struct.keys()) == ["Brillouin"], f"The structure of the data is not correct"
    assert list(struct["Brillouin"].keys()) == ["Brillouin_type","Test"], f"The structure of the data is not correct"
    assert list(struct["Brillouin"]["Test"].keys()) == ["Brillouin_type","Test_0"], f"The structure of the data is not correct"
    assert list(struct["Brillouin"]["Test"]["Test_0"].keys()) == ["Brillouin_type","Raw_data"], f"The structure of the data is not correct"
    assert list(struct["Brillouin"]["Test"]["Test_0"]["Raw_data"].keys()) == ["Brillouin_type"], f"The structure of the data is not correct"
    os.remove(directory+"/test_1.h5")

def test_save_as_hdf5():
    directory=os.path.dirname(os.path.abspath(__file__))
    w = Wrapper()
    w.create_group("Test", parent_group="Brillouin")
    assert "temp.h5" in os.listdir(directory), f"The file 'temp.h5' already exists in the directory {directory}"
    w.save_as_hdf5(filepath=directory+"/test_1.h5", overwrite=True)
    assert "test_1.h5" in os.listdir(directory), f"The file 'test_1.h5' does not exist in the directory {directory}"
    assert "temp.h5" not in os.listdir(directory), f"The file 'temp.h5' still exists in the directory {directory}"
    try: w.save_as_hdf5(filepath=directory+"/test_1.h5", overwrite=False)
    except WrapperError_Overwrite: pass
    os.remove(directory+"/test_1.h5")

def test_set_attributes():
    directory = os.path.dirname(os.path.realpath(__file__))
    w = Wrapper(filepath=directory+"/test_1.h5")
    dic = {"Raw_data": np.random.random(100)}
    w.add_dictionnary(dic, parent_group="Brillouin", name_group="Test", brillouin_type="Measure")
    attributes = {"MEASURE.Sample": "Water", 
                  "FILEPROP.Name": "test"}
    w.set_attributes_data(attributes=attributes, path="Brillouin/Test", overwrite=True)
    with h5py.File(directory+"/test_1.h5", 'r') as file:
        assert file["Brillouin"]["Test"].attrs["MEASURE.Sample"] == "Water", f"The attribute 'MEASURE.Sample' does not have the right value"
        assert file["Brillouin"]["Test"].attrs["FILEPROP.Name"] == "test", f"The attribute 'FILEPROP.Name' does not have the right value"
    try: w.set_attributes_data(attributes=attributes, path="Brillouin/Test", overwrite=False)
    except WrapperError_Overwrite: pass
    try: w.set_attributes_data(attributes=attributes, path="Wrong_path", overwrite=True)
    except WrapperError_StructureError: pass
    os.remove(directory+"/test_1.h5")
 


if __name__ == "__main__":
    test_init()
    test_get_item_()
    test_add_()
    test_add_hdf5()
    test_add_dictionnary()
    test_add_abscissa()
    test_add_raw_data()
    test_add_PSD()
    test_add_frequency()
    test_add_treated_data()
    test_create_group()
    test_delete_element()

    # test_set_attributes()
    # test_get_attributes()
    # test_get_structure()
    # test_save_as_hdf5()