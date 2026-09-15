from pathlib import Path
import pytest
import numpy as np
import os
import shutil
import tempfile
import h5py

from HDF5_BLS.wrapper import Wrapper_file, HDF5_BLS_Version, is_tempfile, HDF5_group, HDF5_dataset
from HDF5_BLS.errors import (
    WrapperError,
    WrapperError_ArgumentType,
    WrapperError_FileNotFound,
    WrapperError_Overwrite,
    WrapperError_Save,
    WrapperError_StructureError,
)

@pytest.fixture
def temp_hdf5_file():
    temp_dir = tempfile.mkdtemp()
    path = os.path.join(temp_dir, "test.h5")
    yield path
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

@pytest.fixture
def wrapper_h5py_instance(temp_hdf5_file: str):
    wrp = Wrapper_file(filepath=temp_hdf5_file)
    yield wrp
    try:
        wrp.close(delete_temp_file=True)
    except Exception:
        pass

def test_init_creates_wrapper_h5py(temp_hdf5_file: str):
    # Default temporary file initialization
    w = Wrapper_file()
    try:
        assert isinstance(w, h5py.File)
        assert isinstance(w, Wrapper_file)
        assert is_tempfile(w.filepath)
        assert list(w.keys()) == ["Brillouin"]
        assert w["Brillouin"].attrs["Brillouin_type"] == "Root"
        assert w["Brillouin"].attrs["HDF5_BLS_version"] == HDF5_BLS_Version
        assert w.filepath == w.filename
    finally:
        w.close(delete_temp_file=True)

    # Specific filepath initialization
    w2 = Wrapper_file(filepath=temp_hdf5_file)
    try:
        assert isinstance(w2, Wrapper_file)
        assert w2.filepath == temp_hdf5_file
        assert list(w2.keys()) == ["Brillouin"]
        assert w2["Brillouin"].attrs["Brillouin_type"] == "Root"
    finally:
        w2.close()

def test_context_manager(temp_hdf5_file: str):
    with Wrapper_file(filepath=temp_hdf5_file) as f:
        assert isinstance(f, Wrapper_file)
        f.create_group("Measure", parent_group="Brillouin", brillouin_type="Measure")
        assert "Brillouin/Measure" in f
    # Outside context manager, file should be closed
    assert not f.id.valid

def test_native_h5py_indexing_and_get_data(wrapper_h5py_instance: Wrapper_file):
    w = wrapper_h5py_instance
    group = w["Brillouin"]
    assert isinstance(group, h5py.Group)

    # Direct creation of dataset
    dset = group.create_dataset("direct_data", data=np.arange(10))
    assert isinstance(w["Brillouin/direct_data"], h5py.Dataset)
    # Native slicing without loading the entire dataset into memory
    assert np.array_equal(w["Brillouin/direct_data"][0:5], np.arange(5))
    assert np.array_equal(w["Brillouin/direct_data"][()], np.arange(10))

    # Test get_data
    assert np.array_equal(w.get_data("Brillouin/direct_data"), np.arange(10))

    # Test get_data with sampling matrix size attribute
    w.add_attributes({"MEASURE.Sampling_Matrix_Size_(Nx,Ny,Nz)_()": "2,5,1"}, parent_group="Brillouin/direct_data")
    reshaped = w.get_data("Brillouin/direct_data")
    assert reshaped.shape == (2, 5, 1, 1)

def test_add_dictionary_and_specific_adders(wrapper_h5py_instance: Wrapper_file):
    w = wrapper_h5py_instance
    dic = {
        "Raw_data": {"Name": "Raw", "Data": np.random.random((5, 5, 10))},
        "PSD": {"Name": "PSD", "Data": np.random.random((5, 5, 10))},
        "Frequency": {"Name": "Frequency", "Data": np.arange(10)},
        "Attributes": {"FILEPROP.Author": "Test Author"}
    }
    w.add_dictionary(dic, parent_group="Brillouin/Measure", create_group=True, brillouin_type_parent_group="Measure")
    assert "Brillouin/Measure" in w
    assert "Raw" in w["Brillouin/Measure"]
    assert "PSD" in w["Brillouin/Measure"]
    assert "Frequency" in w["Brillouin/Measure"]
    assert w["Brillouin/Measure"].attrs["FILEPROP.Author"] == "Test Author"

    # Specific add methods
    w.add_frequency(np.linspace(0, 10, 50), parent_group="Brillouin/Measure", name="Freq2", overwrite=True)
    assert "Freq2" in w["Brillouin/Measure"]
    assert w.get_type("Brillouin/Measure/Freq2", return_Brillouin_type=True) == "Frequency"

    w.add_PSD(np.ones((5, 5, 50)), parent_group="Brillouin/Measure", name="PSD2", overwrite=True)
    assert "PSD2" in w["Brillouin/Measure"]
    assert w.get_type("Brillouin/Measure/PSD2", return_Brillouin_type=True) == "PSD"

    w.add_abscissa(np.arange(5), parent_group="Brillouin/Measure", name="X_axis", unit="um", dim_start=0, dim_end=1)
    assert "X_axis" in w["Brillouin/Measure"]
    assert w.get_type("Brillouin/Measure/X_axis", return_Brillouin_type=True) == "Abscissa_0_1"

    # Treated data
    w.add_treated_data(parent_group="Brillouin/Measure", name_group="Treat_1", shift=np.ones((5, 5)), linewidth=np.zeros((5, 5)))
    assert "Brillouin/Measure/Treat_1" in w
    assert "Shift" in w["Brillouin/Measure/Treat_1"]
    assert "Linewidth" in w["Brillouin/Measure/Treat_1"]

def test_query_methods(wrapper_h5py_instance: Wrapper_file):
    w = wrapper_h5py_instance
    w.add_attributes({"FILEPROP.Experiment": "Brillouin Test"}, parent_group="Brillouin")
    w.create_group("Measure", parent_group="Brillouin", brillouin_type="Measure")
    w.add_frequency(np.arange(10), parent_group="Brillouin/Measure", name="Frequency")

    # get_attributes
    attrs = w.get_attributes("Brillouin/Measure/Frequency")
    assert attrs["FILEPROP.Experiment"] == "Brillouin Test"
    assert attrs["Brillouin_type"] == "Frequency"

    # get_children_elements
    children = w.get_children_elements("Brillouin")
    assert "Measure" in children
    measure_children = w.get_children_elements("Brillouin/Measure", Brillouin_type="Frequency")
    assert measure_children == ["Frequency"]

    # get_type
    assert w.get_type("Brillouin/Measure") == HDF5_group
    assert w.get_type("Brillouin/Measure/Frequency") == HDF5_dataset
    assert w.get_type("Brillouin/Measure", return_Brillouin_type=True) == "Measure"
    assert w.get_type("Brillouin/Measure/Frequency", return_Brillouin_type=True) == "Frequency"

    # get_structure
    struct = w.get_structure()
    assert "Brillouin" in struct
    assert "Measure" in struct["Brillouin"]

def test_manipulation_methods(wrapper_h5py_instance: Wrapper_file):
    w = wrapper_h5py_instance
    grp = w.create_group("TestGroup", parent_group="Brillouin", brillouin_type="Measure")
    assert isinstance(grp, h5py.Group)
    assert "Brillouin/TestGroup" in w

    # change_brillouin_type
    w.change_brillouin_type("Brillouin/TestGroup", "Calibration_spectrum")
    assert w.get_type("Brillouin/TestGroup", return_Brillouin_type=True) == "Calibration_spectrum"

    # change_name
    w.change_name("Brillouin/TestGroup", "RenamedGroup")
    assert "Brillouin/RenamedGroup" in w
    assert "Brillouin/TestGroup" not in w

    # delete_element
    w.delete_element("Brillouin/RenamedGroup")
    assert "Brillouin/RenamedGroup" not in w

def test_combine_datasets(wrapper_h5py_instance: Wrapper_file):
    w = wrapper_h5py_instance
    w.create_group("Measure1", parent_group="Brillouin", brillouin_type="Measure")
    w.create_group("Measure2", parent_group="Brillouin", brillouin_type="Measure")
    w.add_frequency(np.arange(10), parent_group="Brillouin/Measure1", name="Freq")
    w.add_frequency(np.arange(10) * 2, parent_group="Brillouin/Measure2", name="Freq")

    w.combine_datasets(["Brillouin/Measure1/Freq", "Brillouin/Measure2/Freq"], parent_group="Brillouin/Combined", name="AllFreq")
    assert "Brillouin/Combined/AllFreq" in w
    combined_data = w["Brillouin/Combined/AllFreq"][()]
    assert combined_data.shape == (2, 10)

def test_crop_region_of_interest(wrapper_h5py_instance: Wrapper_file):
    w = wrapper_h5py_instance
    w.create_group("Measure", parent_group="Brillouin", brillouin_type="Measure")
    freq = np.linspace(0, 100, 101)
    psd = np.ones((1, 101))
    w.add_frequency(freq, parent_group="Brillouin/Measure", name="Freq")
    w.add_PSD(psd, parent_group="Brillouin/Measure", name="PSD")

    w.crop_region_of_interest("Brillouin/Measure", ROI=[[20, 40]])
    cropped_freq = w["Brillouin/Measure/Freq"][()]
    assert cropped_freq[0] == 20
    assert cropped_freq[-1] == 40

def test_export_and_save(wrapper_h5py_instance: Wrapper_file, temp_hdf5_file: str):
    w = wrapper_h5py_instance
    w.create_group("Measure", parent_group="Brillouin", brillouin_type="Measure")
    w.add_frequency(np.arange(10), parent_group="Brillouin/Measure", name="Freq")

    # Export dataset
    npy_path = temp_hdf5_file + "_export.npy"
    try:
        w.export_dataset("Brillouin/Measure/Freq", npy_path, export_type=".npy")
        assert os.path.isfile(npy_path)
        loaded = np.load(npy_path)
        assert np.array_equal(loaded, np.arange(10))
    finally:
        if os.path.isfile(npy_path):
            os.remove(npy_path)

    # Export group
    export_h5 = temp_hdf5_file + "_group.h5"
    try:
        w.export_group("Brillouin/Measure", export_h5, overwrite=True)
        assert os.path.isfile(export_h5)
        with h5py.File(export_h5, 'r') as f_exp:
            assert "Brillouin" in f_exp
            assert "Measure" in f_exp["Brillouin"]
            assert "Freq" in f_exp["Brillouin/Measure"]
    finally:
        if os.path.isfile(export_h5):
            os.remove(export_h5)

def test_add_wrappers(temp_hdf5_file: str):
    dir_path = os.path.dirname(temp_hdf5_file)
    p1 = os.path.join(dir_path, "wrp1.h5")
    p2 = os.path.join(dir_path, "wrp2.h5")

    w1 = Wrapper_file(filepath=p1)
    w2 = Wrapper_file(filepath=p2)
    try:
        w1.create_group("M1", parent_group="Brillouin", brillouin_type="Measure")
        w2.create_group("M2", parent_group="Brillouin", brillouin_type="Measure")

        w_combined = w1 + w2
        assert isinstance(w_combined, Wrapper_file)
        assert "Brillouin/M1" in w_combined
        assert "Brillouin/M2" in w_combined
        w_combined.close(delete_temp_file=True)
    finally:
        w1.close(delete_temp_file=True)
        w2.close(delete_temp_file=True)

def test_close_and_repack():
    w = Wrapper_file()
    temp_path = w.filepath
    w.save = True

    with pytest.raises(WrapperError_Save):
        w.close()

    w.close(delete_temp_file=True)
    assert not os.path.exists(temp_path)
