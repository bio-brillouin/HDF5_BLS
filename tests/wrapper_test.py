from pathlib import Path
import pytest
import numpy as np
import os
import shutil
import tempfile
import h5py
from HDF5_BLS.wrapper import Wrapper, HDF5_BLS_Version
from HDF5_BLS.WrapperError import *

# Fixture to create a temporary HDF5 file for testing
@pytest.fixture
def temp_hdf5_file():
    path = tempfile.mktemp(suffix=".h5")
    return path

# Fixture to create a Wrapper instance using the temporary HDF5 file
@pytest.fixture
def wrapper_instance(temp_hdf5_file: str):
    return Wrapper(filepath=temp_hdf5_file)

# Test Wrapper initialization and file creation
def test_init_creates_wrapper(temp_hdf5_file: str):
    # Initialize the wrapper with no arguments
    directory = tempfile.gettempdir()
    w = Wrapper()

    # Check if a temporary file is created in the system's temp directory
    tempdir = tempfile.gettempdir()
    # Normalize paths for comparison
    filepath = os.path.abspath(w.filepath)
    tempdir = os.path.abspath(tempdir)
    assert os.path.commonpath([filepath, tempdir]) == tempdir, f"temp.h5 not found in {tempdir}"

    # Remove the temporary file
    os.remove(w.filepath)

    # Create a new wrapper by specifying the path of the file
    w = Wrapper(filepath = directory+"/test_1.h5")
    assert isinstance(w, Wrapper), f"The wrapper is not an instance of the Wrapper class"
    assert w.filepath == directory+"/test_1.h5", f"The wrapper does not have the right filepath"
    assert os.path.isfile(directory+"/test_1.h5"), f"test_1.h5 not found in {directory}"
    with h5py.File(w.filepath, 'r') as file:
        assert list(file.keys()) == ["Brillouin"], f"At initialization the file does not match the initial structure" # Check that only one group exists at initialization
        assert file["Brillouin"].attrs["Brillouin_type"] == "Root", f"At initialization the root group does not have the right Brillouin_type" # Check that the group is of type "Root"
        assert file["Brillouin"].attrs["HDF5_BLS_version"] == HDF5_BLS_Version, f"At initialization the root group does not have the right HDF5_BLS_version" # Check that the group is of type "Root"
    os.remove(directory+"/test_1.h5")

# Test __getitem__ magic method for data access
def test_getitem_returns_data(wrapper_instance: Wrapper):
    # Setup: create a dataset
    with h5py.File(wrapper_instance.filepath, 'a') as f:
        group = f["Brillouin"]
        group.create_dataset("test_data", data=np.arange(10))
    assert isinstance(wrapper_instance["Brillouin/test_data"], np.ndarray)
    arr = wrapper_instance["Brillouin/test_data"]
    assert np.array_equal(arr, np.arange(10))
    os.remove(wrapper_instance.filepath)

# Test __add__ magic method for combining wrappers
def test_add_combines_wrappers(temp_hdf5_file: str):
    # Create two wrappers with minimal structure
    wrp1 = Wrapper(filepath=temp_hdf5_file)
    with h5py.File(temp_hdf5_file, 'a') as file:
        file["Brillouin"].create_dataset("test_data_1", data=np.arange(10))

    path2 = tempfile.mktemp(suffix=".h5")
    wrp2 = Wrapper(filepath=path2)
    with h5py.File(wrp2.filepath, 'a') as file:
        file["Brillouin"].create_dataset("test_data_2", data=np.arange(10))

    # Combine the two wrappers
    new_wrp = wrp1 + wrp2
    assert isinstance(new_wrp, Wrapper)
    assert new_wrp.get_children_elements("Brillouin") == ["test_data_1", "test_data_2"]
    os.remove(path2)
    os.remove(temp_hdf5_file)

# Test adding an HDF5 file to the wrapper
def test_add_hdf5_adds_file(wrapper_instance: Wrapper, temp_hdf5_file: str):
    # Create a source file
    wrp = Wrapper(filepath = temp_hdf5_file)
    with h5py.File(temp_hdf5_file, 'a') as f:
        f["Brillouin"].create_dataset("data", data=np.arange(5))

    wrapper_instance.add_hdf5(temp_hdf5_file)

    with h5py.File(wrapper_instance.filepath, 'r') as f:
        assert temp_hdf5_file.split("/")[-1][:-3] in f["Brillouin"]
        assert "data" in f["Brillouin"][temp_hdf5_file.split("/")[-1][:-3]]
    
    os.remove(temp_hdf5_file)

# Test adding a dictionary using add_dictionary
def test_add_dictionary(wrapper_instance: Wrapper):
    # Create a demo dictionary
    dic = {"Raw_data": {"Name": "Measure Water raw",
                        "Data": np.random.random((50,50,100))},
           "PSD": {"Name": "Measure Water PSD",
                        "Data": np.random.random((50,50,100))},
           "Frequency": {"Name": "Frequency",
                        "Data": np.random.random((50,50,100))},
           "Abscissa_x": {"Name":"x", 
                          "Data":np.linspace(0,10,50), 
                          "Units":"um",
                          "Dim_start":0, 
                          "Dim_end":1},
           "Abscissa_y": {"Name":"y", 
                          "Data":np.linspace(0,10,50), 
                          "Units":"um",
                          "Dim_start":0, 
                          "Dim_end":1},
           "Attribute": {"SPECTROMETER.Type": "TFP",
                          "SAMPLE.Name": "Water"}}
    # Testing adding data without specifying anything
    try:
        wrapper_instance.add_dictionary()
    except TypeError:
        pass

    # Testing adding data without specifying parent group
    try:
        wrapper_instance.add_dictionary(dic)
    except TypeError:
        pass

    # Testing adding data with a wrong parent group
    try:
        wrapper_instance.add_dictionary(dic, parent_group="Wrong_group")
    except WrapperError_StructureError:
        pass

    # Testing adding data while creating a new group without a Brillouin_type
    try:
        wrapper_instance.add_dictionary(dic, parent_group="Brillouin/Measure", create_group=True)
    except WrapperError_StructureError:
        pass
    
    # Testing adding data while creating a new group with a wrong Brillouin_type
    try:
        wrapper_instance.add_dictionary(dic, parent_group="Brillouin/Measure", create_group=True, brillouin_type_parent_group="Wrong_type")
    except WrapperError_StructureError:
        pass

    # Testing adding data while creating a new group with a correct Brillouin_type
    wrapper_instance.add_dictionary(dic, parent_group="Brillouin/Measure", create_group=True, brillouin_type_parent_group="Measure")
    with h5py.File(wrapper_instance.filepath, 'r') as file:
        assert "Measure" in list(file["Brillouin"].keys()), f"The group does not exist in the file"
        assert file["Brillouin"]["Measure"].attrs["Brillouin_type"] == "Measure", f"The group does not have the right Brillouin_type"
        assert file["Brillouin"]["Measure"]["Measure Water raw"].shape == (50,50,100), f"The dataset 'Raw_data' does not have the right shape"
        assert file["Brillouin"]["Measure"].attrs["SPECTROMETER.Type"] == "TFP", f"The dataset 'Raw_data' does not have the right SPECTROMETER.Type"
    
    # Testing adding a second raw data
    dic = {"Raw_data": {"Name": "Measure 2",
                        "Data": np.random.random((50,50,100))}}
    try: wrapper_instance.add_dictionary(dic, parent_group="Brillouin/Measure")
    except WrapperError_Overwrite: pass

    # Testing adding a second dataset with same name
    dic = {"PSD": {"Name": "Measure Water PSD",
                        "Data": np.random.random((50,50,100))}}
    try: wrapper_instance.add_dictionary(dic, parent_group="Brillouin/Measure")
    except WrapperError_Overwrite: pass

    # Testing adding a shift dataset in a Measure group
    dic = {"Shift": {"Name": "Shift",
                        "Data": np.random.random((50,50))}}
    try: wrapper_instance.add_dictionary(dic, parent_group="Brillouin/Measure")
    except WrapperError_StructureError: pass

    # Testing adding a dataset in a calibration group
    dic = {"Raw_data": {"Name": "Measure Water raw",
                        "Data": np.random.random((50,50,100))},
           "PSD": {"Name": "Measure Water PSD",
                        "Data": np.random.random((50,50,100))},
           "Frequency": {"Name": "Frequency",
                        "Data": np.random.random((50,50,100))}}
    wrapper_instance.add_dictionary(dic, parent_group="Brillouin/Calibration", create_group=True, brillouin_type_parent_group="Calibration_spectrum")
    with h5py.File(wrapper_instance.filepath, 'r') as file:
        assert "Calibration" in file["Brillouin"].keys()
        assert "Measure Water raw" in file["Brillouin/Calibration"].keys()
        assert "Measure Water PSD" in file["Brillouin/Calibration"].keys()
        assert "Frequency" in file["Brillouin/Calibration"].keys()

    # Testing adding a shift dataset in a treatment group
    dic = {"Shift": {"Name": "Shift",
                        "Data": np.random.random((50,50))}}
    wrapper_instance.add_dictionary(dic, parent_group="Brillouin/Measure/Treatment", create_group=True, brillouin_type_parent_group="Treatment")
    with h5py.File(wrapper_instance.filepath, 'r') as file:
        assert "Treatment" in file["Brillouin/Measure"].keys()
        assert "Shift" in file["Brillouin/Measure/Treatment"].keys()
    
    # Removing temporary file
    os.remove(wrapper_instance.filepath)

# Test changing the Brillouin type of a group
def test_change_brillouin_type(wrapper_instance: Wrapper):
    # Setup: create a group with a specific Brillouin_type
    with h5py.File(wrapper_instance.filepath, 'a') as f:
        grp = f.create_group("Brillouin/test")
        grp.attrs["Brillouin_type"] = "Measure"

    # Test changing Brillouin type on a non-existing path
    try: wrapper_instance.change_brillouin_type("Brillouin/wrong_path", "Impulse_response")
    except WrapperError_StructureError: pass

    # Test changing Brillouin type to an invalid type
    try: wrapper_instance.change_brillouin_type("Brillouin/test", "Wrong_type")
    except WrapperError_ArgumentType: pass

    # Test successful change of Brillouin type
    assert wrapper_instance.get_type(path = "Brillouin/test",  return_Brillouin_type=True) == "Measure"
    wrapper_instance.change_brillouin_type("Brillouin/test", "Impulse_response")
    assert wrapper_instance.get_type(path = "Brillouin/test",  return_Brillouin_type=True) == "Impulse_response"

    os.remove(wrapper_instance.filepath)

# Test changing the name of an element
def test_change_name(wrapper_instance: Wrapper):
    # Setup: create a group with a specific Brillouin_type
    with h5py.File(wrapper_instance.filepath, 'a') as f:
        grp = f.create_group("Brillouin/old_name")
        grp.attrs["Brillouin_type"] = "Measure"
    
    # Test changing name on a non-existing path
    try: wrapper_instance.change_name("Brillouin/wrong_path", "new_name")
    except WrapperError_StructureError: pass

    # Test successful change of name
    wrapper_instance.change_name("Brillouin/old_name", "new_name")
    with h5py.File(wrapper_instance.filepath, 'r') as f:
        assert "new_name" in f["Brillouin"]

    os.remove(wrapper_instance.filepath)

# Test closing the wrapper and deleting the temp file
def test_close_deletes_temp(wrapper_instance: Wrapper):
    # Get the path of the temporary file and set the save flag to True
    temp_path = wrapper_instance.filepath
    wrapper_instance.save = True

    # Test closing the wrapper without expressely saying that we want to delete the temporary file
    try: wrapper_instance.close()
    except WrapperError_Save: pass

    # Test closing the wrapper and deleting the temporary file
    wrapper_instance.close(delete_temp_file=True)
    assert not os.path.exists(temp_path)

# Test combining datasets into one
def test_combine_datasets(wrapper_instance: Wrapper):
    # Setup: create three datasets
    with h5py.File(wrapper_instance.filepath, 'a') as f:
        f["Brillouin"].create_group("Measure 1")
        f["Brillouin/Measure 1"].attrs["Brillouin_type"] = "Measure"
        f["Brillouin/Measure 1"].create_dataset("d1-10", data=np.arange(10))
        f["Brillouin/Measure 1/d1-10"].attrs["Brillouin_type"] = "Raw_data"
        f["Brillouin"].create_group("Measure 2")
        f["Brillouin/Measure 2"].attrs["Brillouin_type"] = "Measure"
        f["Brillouin/Measure 2"].create_dataset("d2-10", data=np.arange(10))
        f["Brillouin/Measure 2/d2-10"].attrs["Brillouin_type"] = "Raw_data"
        f["Brillouin"].create_group("Measure 3")
        f["Brillouin/Measure 3"].attrs["Brillouin_type"] = "Measure"
        f["Brillouin/Measure 3"].create_dataset("d3-20", data=np.arange(20))
        f["Brillouin/Measure 3/d3-20"].attrs["Brillouin_type"] = "Raw_data"

    # Try adding a group as a dataset
    try: wrapper_instance.combine_datasets(datasets = ["Brillouin", "Brillouin/Measure 1/d1-10"], parent_group="Brillouin/Combined", name="combined")
    except WrapperError_ArgumentType: pass

    # Try adding a dataset with the same name
    try: wrapper_instance.combine_datasets(datasets = ["Brillouin/Measure 1/d1-10", "Brillouin/Measure 2/d2-10"], parent_group="Brillouin/Measure 1", name="d1-10")
    except WrapperError_Overwrite: pass

    # Try adding datasets with different shapes
    try: wrapper_instance.combine_datasets(datasets = ["Brillouin/Measure 1/d1-10", "Brillouin/Measure 3/d3-20"], parent_group="Brillouin/Measure", name="combined")
    except WrapperError_ArgumentType: pass
    
    # Test successful addition of datasets
    wrapper_instance.combine_datasets(datasets = ["Brillouin/Measure 1/d1-10", "Brillouin/Measure 2/d2-10"], parent_group="Brillouin/Measure", name="combined")
    with h5py.File(wrapper_instance.filepath, 'r') as f:
        assert "Measure" in f["Brillouin"]
        assert f["Brillouin/Measure/combined"].shape == (2, 10)
        assert f["Brillouin/Measure/combined"].attrs["Brillouin_type"] == "Raw_data"
    
    os.remove(wrapper_instance.filepath)

# Test compatibility_changes method (should not raise)
def test_compatibility_changes(wrapper_instance: Wrapper):
    # TEST TO BE UPDATED WITH NEW VERSIONS OF LIBRARY
    wrapper_instance.compatibility_changes()
    os.remove(wrapper_instance.filepath)

# Test copying a dataset within the file
def test_copy_dataset(wrapper_instance: Wrapper):
    with h5py.File(wrapper_instance.filepath, 'a') as f:
        group = f["Brillouin"].create_group("Measure")
        group.attrs["Brillouin_type"] = "Measure"
        ds = group.create_dataset("data", data=np.arange(5))
        ds.attrs["Brillouin_type"] = "Raw_data"
        group2 = f["Brillouin"].create_group("Measure2")
        group2.attrs["Brillouin_type"] = "Measure"
    wrapper_instance.copy_dataset("Brillouin/Measure/data", "Brillouin/Measure2")
    with h5py.File(wrapper_instance.filepath, 'r') as f:
        assert "data" in f["Brillouin/Measure2"]
        assert np.array_equal(f["Brillouin/Measure2/data"][:], np.arange(5))
    
    os.remove(wrapper_instance.filepath)

# Test creating a new group
def test_create_group(wrapper_instance: Wrapper):
    # Create a new group under a wrong parent group
    try: wrapper_instance.create_group("new_group", parent_group="Wrong_group")
    except WrapperError_StructureError: pass

    # Create a new group under a correct parent group
    wrapper_instance.create_group("new_group", parent_group="Brillouin")

    # Try creating a group with the same name
    try: wrapper_instance.create_group("new_group", parent_group="Brillouin")
    except WrapperError_Overwrite: pass

    # Create a group with a custom Brillouin_type
    wrapper_instance.create_group("new_group2", parent_group="Brillouin", brillouin_type="Measure")

    # Check that the groups were created correctly
    with h5py.File(wrapper_instance.filepath, 'r') as f:
        assert "new_group" in f["Brillouin"]
        assert "new_group2" in f["Brillouin"]
        assert f["Brillouin/new_group"].attrs["Brillouin_type"] == "Root"
        assert f["Brillouin/new_group2"].attrs["Brillouin_type"] == "Measure"
    
    os.remove(wrapper_instance.filepath)

# Test deleting an element from the file
def test_delete_element(wrapper_instance: Wrapper):
    with h5py.File(wrapper_instance.filepath, 'a') as f:
        # Setup: create a dataset
        group = f["Brillouin"].create_group("Measure")
        group.attrs["Brillouin_type"] = "Measure"
        ds = group.create_dataset("data", data=np.arange(5))
        ds.attrs["Brillouin_type"] = "Raw_data"

    # Test: delete the dataset
    wrapper_instance.delete_element("Brillouin/Measure/data")

    # Check that the dataset was deleted and need_for_repack is set to True
    assert wrapper_instance.need_for_repack == True
    with h5py.File(wrapper_instance.filepath, 'r') as f:
        assert "data" not in f["Brillouin/Measure"]
    
    os.remove(wrapper_instance.filepath)

# Test exporting a dataset to a file
def test_export_dataset(wrapper_instance: Wrapper):
    tmp_path = tempfile.gettempdir()+"/HDF5_BLS_tests"
    # Setup: create datasets of various dimensions
    with h5py.File(wrapper_instance.filepath, 'a') as f:
        group2D = f["Brillouin"].create_group("Measure 2D")
        group2D.attrs["Brillouin_type"] = "Measure"
        ds2D = f["Brillouin/Measure 2D"].create_dataset("data", data=np.random.random((5, 5)))
        ds2D.attrs["Brillouin_type"] = "Raw_data"

        group3D = f["Brillouin"].create_group("Measure 3D")
        group3D.attrs["Brillouin_type"] = "Measure"
        ds3D = f["Brillouin/Measure 3D"].create_dataset("data", data=np.random.random((5, 5, 5)))
        ds3D.attrs["Brillouin_type"] = "Raw_data"

    # Setup temporary directory for exports
    os.mkdir(tmp_path)

    # Test exporting 2D dataset without specifying export type
    export_path = f"{tmp_path}/export_2D"
    wrapper_instance.export_dataset(path = "Brillouin/Measure 2D/data", filepath = str(export_path), export_type = ".npy")
    assert os.path.exists(export_path+".npy"), f"The file '{export_path}' does not exist."
    wrapper_instance.export_dataset(path = "Brillouin/Measure 2D/data", filepath = str(export_path), export_type = ".csv")
    assert os.path.exists(export_path+".csv"), f"The file '{export_path}' does not exist."
    wrapper_instance.export_dataset(path = "Brillouin/Measure 2D/data", filepath = str(export_path), export_type = ".xlsx")
    assert os.path.exists(export_path+".xlsx"), f"The file '{export_path}' does not exist."

    # Test exporting 2D dataset specifying export type
    export_path = f"{tmp_path}/export_2D.npy"
    wrapper_instance.export_dataset(path = "Brillouin/Measure 2D/data", filepath = str(export_path), export_type = ".npy")
    assert os.path.exists(export_path), f"The file '{export_path}' does not exist."
    wrapper_instance.export_dataset(path = "Brillouin/Measure 2D/data", filepath = str(export_path), export_type = ".xlsx")
    assert os.path.exists(export_path+".xlsx"), f"The file '{export_path}' does not exist."

    # Test exporting 3D dataset uing numpy and then xlsx
    export_path = f"{tmp_path}/export_3D"
    wrapper_instance.export_dataset(path = "Brillouin/Measure 3D/data", filepath = str(export_path), export_type = ".npy")
    assert os.path.exists(export_path+".npy"), f"The file '{export_path}' does not exist."
    try: wrapper_instance.export_dataset(path = "Brillouin/Measure 3D/data", filepath = str(export_path), export_type = ".xlsx")
    except WrapperError_ArgumentType: pass

    os.remove(wrapper_instance.filepath)
    for f in os.listdir(tmp_path):
        os.remove(os.path.join(tmp_path, f))
    os.rmdir(tmp_path)

# Test exporting a group to a file
def test_export_group(wrapper_instance: Wrapper):
    tmp_path = "/".join(wrapper_instance.filepath.split("/")[:-1])
    # Setup: Create an initial HDF5 file
    with h5py.File(wrapper_instance.filepath, 'a') as f:
        group = f["Brillouin"].create_group("Measure")
        group.attrs["Brillouin_type"] = "Measure"
        psd = group.create_dataset("PSD", data = np.random.random((5,5)))
        psd.attrs["Brillouin_type"] = "PSD"
        psd = group.create_dataset("Frequency", data = np.arange(5))
        psd.attrs["Brillouin_type"] = "Frequency"
        treat_group = group.create_group("Treatment")
        treat_group.attrs["Brillouin_type"] = "Treatment"
        shift = treat_group.create_dataset("Shift", data = np.arange(10))
        shift.attrs["Brillouin_type"] = "Shift"
        linewidth = treat_group.create_dataset("Linewidth", data = np.arange(10))
        linewidth.attrs["Brillouin_type"] = "Linewidth"
    
    export_path = f"{tmp_path}/export_group.h5"

    # Test exporting a non-existing element
    try: wrapper_instance.export_group("Brillouin/Measure/Non_existing", str(export_path))
    except WrapperError_StructureError: pass

    # Test exporting a dataset
    try: wrapper_instance.export_group("Brillouin/Measure/PSD", str(export_path))
    except WrapperError_ArgumentType: pass

    # Test exporing a treatment group
    try: wrapper_instance.export_group("Brillouin/Measure/Treatment", str(export_path))
    except WrapperError_ArgumentType: pass

    # Test successful export of a group
    wrapper_instance.export_group("Brillouin/Measure", str(export_path))
    assert os.path.exists(export_path)
    with h5py.File(export_path, 'r') as f:
        assert "Measure" in f["Brillouin"]
        assert "PSD" in f["Brillouin/Measure"]
        assert "Frequency" in f["Brillouin/Measure"]
        assert "Treatment" in f["Brillouin/Measure"]
        assert "Shift" in f["Brillouin/Measure/Treatment"]
        assert "Linewidth" in f["Brillouin/Measure/Treatment"]

    os.remove(export_path)
    os.remove(wrapper_instance.filepath)

# Test exporting an image from a dataset
def test_export_image(wrapper_instance: Wrapper):
    tmp_path = "/".join(wrapper_instance.filepath.split("/")[:-1])
    # Setup: create a 2D dataset
    arr = np.random.rand(10, 10)
    with h5py.File(wrapper_instance.filepath, 'a') as f:
        group = f["Brillouin"].create_group("Measure")
        group.attrs["Brillouin_type"] = "Measure"
        ds = group.create_dataset("img", data=arr)
        ds.attrs["Brillouin_type"] = "Other"
    export_path = f"{tmp_path}/img.png"
    wrapper_instance.export_image("Brillouin/Measure/img", str(export_path))
    assert os.path.exists(export_path)
    os.remove(wrapper_instance.filepath)
    os.remove(export_path)

# Test getting attributes from a group
def test_get_attributes(wrapper_instance: Wrapper):
    data = np.random.random((5,5))
    # Setup: create a dataset
    with h5py.File(wrapper_instance.filepath, 'a') as f:
        group1 = f["Brillouin"].create_group("Group1")
        group1.attrs["Brillouin_type"] = "Root"
        group1.attrs["MEASURE.Sample"] = "Water"
        group1.attrs["SPECTROMETER.Type"] = "TFP"
        group2 = group1.create_group("Group2")
        group2.attrs["Brillouin_type"] = "Measure"
        group2.attrs["MEASURE.Sample"] = "Ethanol"
        ds = group2.create_dataset("data", data=data)
        ds.attrs["Brillouin_type"] = "Raw_data"
    
    # Test getting attributes from a non-existing path
    try: wrapper_instance.get_attributes(path="Brillouin/Wrong_path")
    except WrapperError_StructureError: pass

    # Test getting attributes from an parent group
    attr = wrapper_instance.get_attributes(path="Brillouin/Group1")
    assert attr["MEASURE.Sample"] == "Water", f"The attribute 'MEASURE.Sample' does not have the right value"
    assert attr["SPECTROMETER.Type"] == "TFP", f"The attribute 'SPECTROMETER.Type' does not have the right value"

    # Test getting attributes from a child group of the parent group and check it has the same attributes except the ones overwritten
    attr = wrapper_instance.get_attributes(path="Brillouin/Group1/Group2")
    assert attr["MEASURE.Sample"] == "Ethanol", f"The attribute 'MEASURE.Sample' does not have the right value"
    assert attr["SPECTROMETER.Type"] == "TFP", f"The attribute 'SPECTROMETER.Type' does not have the right value"

    # Test getting attributes from a dataset and check they are the ones they should be
    attr = wrapper_instance.get_attributes(path="Brillouin/Group1/Group2/data")
    assert attr["MEASURE.Sample"] == "Ethanol", f"The attribute 'MEASURE.Sample' does not have the right value"
    assert attr["SPECTROMETER.Type"] == "TFP", f"The attribute 'SPECTROMETER.Type' does not have the right value"

    os.remove(wrapper_instance.filepath)

# Test getting children elements of a group
def test_get_children_elements(wrapper_instance: Wrapper):
    # Setup: create groups and datasets
    with h5py.File(wrapper_instance.filepath, 'a') as f:
        group1 = f["Brillouin"].create_group("Group1")
        group1.attrs["Brillouin_type"] = "Root"
        group1_1 = group1.create_group("Group1")
        group1_1.attrs["Brillouin_type"] = "Measure"
        group1_2 = group1.create_group("Group2")
        group1_2.attrs["Brillouin_type"] = "Calibration_spectrum"
        ds1 = group1_1.create_dataset("data", data=np.random.random((5,5)))
        ds1.attrs["Brillouin_type"] = "Raw_data"
        ds2 = group1_2.create_dataset("data", data=np.random.random((5,5)))
        ds2.attrs["Brillouin_type"] = "Raw_data"

    assert wrapper_instance.get_children_elements() == ["Group1"]
    assert wrapper_instance.get_children_elements("Brillouin") == ["Group1"]
    assert wrapper_instance.get_children_elements("Brillouin/Group1") == ["Group1", "Group2"]
    assert wrapper_instance.get_children_elements("Brillouin/Group1", Brillouin_type="Measure") == ["Group1"]

    os.remove(wrapper_instance.filepath)

# Test getting special groups hierarchy
def test_get_special_groups_hierarchy(wrapper_instance: Wrapper):
    # Setup: create the file
    with h5py.File(wrapper_instance.filepath, 'a') as f:
        group1 = f["Brillouin"].create_group("Group1")
        group1.attrs["Brillouin_type"] = "Root"
        group1_1 = group1.create_group("Group1")
        group1_1.attrs["Brillouin_type"] = "Measure"
        group1_2 = group1.create_group("Group2")
        group1_2.attrs["Brillouin_type"] = "Calibration_spectrum"
        group1_3 = group1.create_group("Group3")
        group1_3.attrs["Brillouin_type"] = "Measure"
        group1_4 = group1.create_group("Group4")
        group1_4.attrs["Brillouin_type"] = "Root"
        group1_4_1 = group1_4.create_group("Group1")
        group1_4_1.attrs["Brillouin_type"] = "Measure"
        ds1 = group1_1.create_dataset("data", data=np.random.random((5,5)))
        ds1.attrs["Brillouin_type"] = "Raw_data"
        ds2 = group1_4_1.create_dataset("data", data=np.random.random((5,5)))
        ds2.attrs["Brillouin_type"] = "Raw_data"
    
    # Test giving a wrong path
    try: wrapper_instance.get_special_groups_hierarchy(path = "Wrong_path")
    except WrapperError_StructureError: pass

    # Check that the function returns the correct hierarchy
    assert wrapper_instance.get_special_groups_hierarchy(path = "Brillouin/Group1/Group1/data") == ["Brillouin/Group1", "Brillouin/Group1/Group4"]
    assert wrapper_instance.get_special_groups_hierarchy(path = "Brillouin/Group1/Group4/Group1/data") == ["Brillouin/Group1", "Brillouin/Group1/Group4"]
    assert wrapper_instance.get_special_groups_hierarchy(path = "Brillouin/Group1/Group4/Group1/data", brillouin_type="Measure") == ['Brillouin/Group1/Group1', 'Brillouin/Group1/Group3', 'Brillouin/Group1/Group4/Group1']
    assert wrapper_instance.get_special_groups_hierarchy(path = "Brillouin/Group1/Group1/data", brillouin_type = "Measure") == ["Brillouin/Group1/Group1","Brillouin/Group1/Group3"]
    assert wrapper_instance.get_special_groups_hierarchy(path = "Brillouin/Group1/Group1/data", brillouin_type = "Calibration_spectrum") == ["Brillouin/Group1/Group2"]
    
    os.remove(wrapper_instance.filepath)

# Test getting the structure of the file
def test_get_structure(wrapper_instance: Wrapper):
    # Setup: create the file
    with h5py.File(wrapper_instance.filepath, 'a') as f:
        group1 = f["Brillouin"].create_group("Test")
        group1.attrs["Brillouin_type"] = "Root"
        ds = group1.create_dataset("Test_0", data=np.random.random((5,5)))
        ds.attrs["Brillouin_type"] = "Raw_data"

    struct = wrapper_instance.get_structure()
    assert list(struct.keys()) == ["Brillouin"], f"The structure of the data is not correct"
    assert list(struct["Brillouin"].keys()) == ["Brillouin_type","Test"], f"The structure of the data is not correct"
    assert list(struct["Brillouin"]["Test"].keys()) == ["Brillouin_type","Test_0"], f"The structure of the data is not correct"
    assert list(struct["Brillouin"]["Test"]["Test_0"].keys()) == ["Brillouin_type"], f"The structure of the data is not correct"
    assert struct["Brillouin"]["Test"]["Test_0"]["Brillouin_type"] == "Raw_data", f"The structure of the data is not correct"
    
    os.remove(wrapper_instance.filepath)

# Test getting the type of an element
def test_get_type(wrapper_instance: Wrapper):
    # Setup: create the file
    with h5py.File(wrapper_instance.filepath, 'a') as f:
        group1 = f["Brillouin"].create_group("Group1")
        group1.attrs["Brillouin_type"] = "Root"
        group1_1 = group1.create_group("Group1")
        group1_1.attrs["Brillouin_type"] = "Measure"
        ds = group1_1.create_dataset("data", data=np.random.random((5,5)))
        ds.attrs["Brillouin_type"] = "Raw_data"
    
    assert wrapper_instance.get_type(path = "Brillouin/Group1") == h5py._hl.group.Group
    assert wrapper_instance.get_type(path = "Brillouin/Group1", return_Brillouin_type = True) == "Root"
    assert wrapper_instance.get_type(path = "Brillouin/Group1/Group1") == h5py._hl.group.Group
    assert wrapper_instance.get_type(path = "Brillouin/Group1/Group1", return_Brillouin_type = True) == "Measure"
    assert wrapper_instance.get_type(path = "Brillouin/Group1/Group1/data") == h5py._hl.dataset.Dataset
    assert wrapper_instance.get_type(path = "Brillouin/Group1/Group1/data", return_Brillouin_type = True) == "Raw_data"

    os.remove(wrapper_instance.filepath)

# Test moving an element within the file
def test_move(wrapper_instance: Wrapper):
    # Setup: Create the file
    with h5py.File(wrapper_instance.filepath, "a") as file:
        group1 = file["Brillouin"].create_group("Group1")
        group1.attrs["Brillouin_type"] = "Root"
        measure = group1.create_group("Measure")
        measure.attrs["Brillouin_type"] = "Measure"
        ds = measure.create_dataset("Raw data", data = np.arange(5))
        ds.attrs["Brillouin_type"] = "Raw_data"
        group2 = file["Brillouin"].create_group("Group2")
        group2.attrs["Brillouin_type"] = "Root"
    
    # Test moving an element that does not exist
    try: wrapper_instance.move(path = "Wrong_path", new_path = "Brillouin/Group2")
    except WrapperError_StructureError: pass

    # Test moving to an existing group
    wrapper_instance.move(path = "Brillouin/Group1/Measure", new_path = "Brillouin/Group2")
    with h5py.File(wrapper_instance.filepath, "r") as file:
        assert "Measure" in file["Brillouin/Group2"].keys()
        assert file["Brillouin/Group2/Measure"].attrs["Brillouin_type"] == "Measure"
        assert list(file["Brillouin/Group2/Measure"].keys()) == ["Raw data"]
        assert file["Brillouin/Group2/Measure/Raw data"].attrs["Brillouin_type"] == "Raw_data"
    
    # Test moving to a non-existing group
    wrapper_instance.move(path = "Brillouin/Group2/Measure", new_path = "Brillouin/Group3")
    with h5py.File(wrapper_instance.filepath, "r") as file:
        assert "Group3" in file["Brillouin"]
        assert "Measure" in file["Brillouin/Group3"].keys()
        assert file["Brillouin/Group3/Measure"].attrs["Brillouin_type"] == "Measure"
        assert list(file["Brillouin/Group3/Measure"].keys()) == ["Raw data"]
        assert file["Brillouin/Group3/Measure/Raw data"].attrs["Brillouin_type"] == "Raw_data"
        
    os.remove(wrapper_instance.filepath)

# Test repacking the file (should not raise)
def test_repack(wrapper_instance: Wrapper):
    # Setup: Create the file
    with h5py.File(wrapper_instance.filepath, "a") as file:
        group1 = file["Brillouin"].create_group("Group1")
        group1.attrs["Brillouin_type"] = "Root"
        measure = group1.create_group("Measure")
        measure.attrs["Brillouin_type"] = "Measure"
        ds = measure.create_dataset("Raw data", data = np.arange(5))
        ds.attrs["Brillouin_type"] = "Raw_data"
        group2 = file["Brillouin"].create_group("Group2")
        group2.attrs["Brillouin_type"] = "Root"
    
    wrapper_instance.repack(force_repack=True)

    with h5py.File(wrapper_instance.filepath, "r") as file:
        assert "Brillouin" in file 
        assert "Brillouin/Group1" in file
        assert "Brillouin/Group1/Measure" in file
        assert "Brillouin/Group1/Measure/Raw data" in file
        assert "Brillouin/Group2" in file

    os.remove(wrapper_instance.filepath)

# Test moving channel dimension to last
def test_move_channel_dimension_to_last(wrapper_instance: Wrapper):
    # Setup: Create the file
    with h5py.File(wrapper_instance.filepath, "a") as file:
        group1 = file["Brillouin"].create_group("Group1")
        group1.attrs["Brillouin_type"] = "Root"
        measure = group1.create_group("Measure")
        measure.attrs["Brillouin_type"] = "Measure"
        ds = measure.create_dataset("Raw data", data = np.random.rand(2, 3, 4))
        ds.attrs["Brillouin_type"] = "Raw_data"
        group2 = file["Brillouin"].create_group("Group2")
        group2.attrs["Brillouin_type"] = "Root"
    
    with h5py.File(wrapper_instance.filepath, "r") as file:
        assert file["Brillouin/Group1/Measure/Raw data"].shape == (2, 3, 4)
    
    wrapper_instance.move_channel_dimension_to_last("Brillouin/Group1/Measure/Raw data", channel_dimension=0)

    with h5py.File(wrapper_instance.filepath, "r") as file:
        assert file["Brillouin/Group1/Measure/Raw data"].shape == (3, 4, 2)
    assert wrapper_instance.need_for_repack == True

    os.remove(wrapper_instance.filepath)

# Test saving as HDF5 file
def test_save_as_hdf5(wrapper_instance: Wrapper):
    # Setup: Create a dataset
    with h5py.File(wrapper_instance.filepath, 'a') as f:
        group = f["Brillouin"].create_group("Group1")
        group.attrs["Brillouin_type"] = "Measure"
        ds = group.create_dataset("Raw data", data=np.arange(5))
        ds.attrs["Brillouin_type"] = "Raw_data"
    
    tmp_path = tempfile.gettempdir()
    old_path = wrapper_instance.filepath
    save_path = tmp_path + "/saved.h5"

    # Try saving the file without removing old file
    wrapper_instance.save_as_hdf5(str(save_path), remove_old_file=False)
    assert os.path.exists(old_path)
    assert os.path.exists(save_path)

    # Try overwriting the file
    try: wrapper_instance.save_as_hdf5(str(old_path))
    except WrapperError_Overwrite: pass
    wrapper_instance.save_as_hdf5(str(old_path), overwrite=True)

    # Try saving the file with removing old file
    wrapper_instance.save_as_hdf5(str(save_path))
    assert not os.path.exists(old_path)
    assert os.path.exists(save_path)

    os.remove(save_path)

# Test saving properties as CSV
def test_save_properties_csv(wrapper_instance: Wrapper):
    import csv
    # Setup: Create the file
    with h5py.File(wrapper_instance.filepath, "a") as f:
        f["Brillouin"].attrs["SPECTROMETER.Type"] = "VIPA"
        group = f["Brillouin"].create_group("Group1")
        group.attrs["Brillouin_type"] = "Measure"
        group.attrs["MEASURE.Sample"] = "Water"
        ds = group.create_dataset("Raw data", data=np.arange(5))
        ds.attrs["Brillouin_type"] = "Raw_data"
    
    tmp_path = tempfile.gettempdir()
    csv_path = f"{tmp_path}/props.csv"
    wrapper_instance.save_properties_csv(str(csv_path), path="Brillouin/Group1/Raw data")

    with open(csv_path, mode='r', encoding='latin1') as csv_file:
        csv_reader = csv.reader(csv_file)
        rows = []
        for row in csv_reader:
            rows.append(row)
    assert len(rows) == 7
    assert rows[2] == ["SPECTROMETER"]
    assert rows[3] == ["SPECTROMETER.Type", "VIPA"]
    assert rows[5] == ["MEASURE"]
    assert rows[6] == ["MEASURE.Sample", "Water"]

    assert os.path.exists(csv_path)

    os.remove(wrapper_instance.filepath)
    os.remove(csv_path)

# # Test adding abscissa data
# def test_add_abscissa(wrapper_instance: Wrapper):
#     arr = np.arange(5)
#     wrapper_instance.add_abscissa(arr, parent_group="Brillouin", name="abscissa")
#     with h5py.File(wrapper_instance.filepath, 'r') as f:
#         assert "abscissa" in f["Brillouin"]

# # Test adding attributes to a group
# def test_add_attributes(wrapper_instance: Wrapper):
#     wrapper_instance.create_group("grp", parent_group="Brillouin")
#     wrapper_instance.add_attributes({"attr": "value"}, parent_group="Brillouin/grp")
#     attrs = wrapper_instance.get_attributes("Brillouin/grp")
#     assert "attr" in attrs

# # Test adding frequency data
# def test_add_frequency(wrapper_instance: Wrapper):
#     arr = np.arange(5)
#     wrapper_instance.add_frequency(arr, parent_group="Brillouin", name="freq")
#     with h5py.File(wrapper_instance.filepath, 'r') as f:
#         assert "freq" in f["Brillouin"]

# # Test adding PSD data
# def test_add_PSD(wrapper_instance: Wrapper):
#     arr = np.arange(5)
#     wrapper_instance.add_PSD(arr, parent_group="Brillouin", name="psd")
#     with h5py.File(wrapper_instance.filepath, 'r') as f:
#         assert "psd" in f["Brillouin"]

# # Test adding raw data
# def test_add_raw_data(wrapper_instance: Wrapper):
#     arr = np.arange(5)
#     wrapper_instance.add_raw_data(arr, parent_group="Brillouin", name="raw")
#     with h5py.File(wrapper_instance.filepath, 'r') as f:
#         assert "raw" in f["Brillouin"]

# # Test adding treated data
# def test_add_treated_data(wrapper_instance: Wrapper):
#     arr = np.arange(5)
#     wrapper_instance.add_treated_data(parent_group="Brillouin", name_group="treated", shift=arr, linewidth=arr)
#     with h5py.File(wrapper_instance.filepath, 'r') as f:
#         assert "treated" in f["Brillouin"]

# # Test clearing empty attributes
# def test_clear_empty_attributes(wrapper_instance: Wrapper):
#     wrapper_instance.create_group("grp", parent_group="Brillouin")
#     wrapper_instance.clear_empty_attributes("Brillouin/grp")
#     # Should not raise

# # Test importing raw data from file
# def test_import_raw_data(wrapper_instance: Wrapper, tmp_path: Path):
#     arr = np.arange(5)
#     raw_path = tmp_path / "raw.npy"
#     np.save(raw_path, arr)
#     wrapper_instance.import_raw_data(str(raw_path), parent_group="Brillouin", name="raw")
#     with h5py.File(wrapper_instance.filepath, 'r') as f:
#         assert "raw" in f["Brillouin"]

# # Test importing other data from file
# def test_import_other(wrapper_instance: Wrapper, tmp_path: Path):
#     arr = np.arange(5)
#     other_path = tmp_path / "other.npy"
#     np.save(other_path, arr)
#     wrapper_instance.import_other(str(other_path), parent_group="Brillouin", name="other")
#     with h5py.File(wrapper_instance.filepath, 'r') as f:
#         assert "other" in f["Brillouin"]

# # Test importing properties data from xlsx file
# def test_import_properties_data(wrapper_instance: Wrapper, tmp_path: Path):
#     # Create dummy xlsx file
#     xlsx_path = tmp_path / "props.xlsx"
#     with open(xlsx_path, "wb") as f:
#         f.write(b"PK\x03\x04")  # minimal zip header for xlsx
#     wrapper_instance.import_properties_data(str(xlsx_path), path="Brillouin")
#     # Should not raise

# # Test updating a property in a group
# def test_update_property(wrapper_instance: Wrapper):
#     wrapper_instance.create_group("grp", parent_group="Brillouin")
#     wrapper_instance.update_property("attr", "value", "Brillouin/grp")
#     attrs = wrapper_instance.get_attributes("Brillouin/grp")
#     assert "attr" in attrs

# # Test printing the structure of the file
# def test_print_structure(wrapper_instance: Wrapper, capsys: pytest.CaptureFixture[str]):
#     wrapper_instance.create_group("grp", parent_group="Brillouin")
#     wrapper_instance.print_structure()
#     captured = capsys.readouterr()
#     assert "grp" in captured.out

# # Test printing metadata of a group
# def test_print_metadata(wrapper_instance: Wrapper, capsys: pytest.CaptureFixture[str]):
#     wrapper_instance.create_group("grp", parent_group="Brillouin")
#     wrapper_instance.print_metadata("Brillouin/grp")
#     captured = capsys.readouterr()
#     assert "grp" in captured.out