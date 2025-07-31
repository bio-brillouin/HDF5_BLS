import pytest
import sys
import os
import datetime

current_dir = os.path.abspath(os.path.dirname(__file__))
relative_path_libs = os.path.join(current_dir, "..", "..", "HDF5_BLS")
absolute_path_libs = os.path.abspath(relative_path_libs)
sys.path.append(absolute_path_libs)
from HDF5_BLS.load_data import load_dat_file, load_image_file, load_general, load_npy_file, load_sif_file
from HDF5_BLS.load_formats.errors import LoadError_creator, LoadError_parameters

def test_load_dat_file():
    filepath = os.path.join(os.path.dirname(__file__), "test_data", "example_GHOST.DAT")
    try: load_dat_file(filepath)
    except LoadError_creator as e: pass
    
    try: load_dat_file(filepath, creator = "TimeDomain")
    except LoadError_parameters as e: pass

    dic = load_dat_file(filepath, creator = "GHOST")
    assert list(dic.keys()) == ["Raw_data", "Attributes"], "FAIL - test_load_dat_file - Structure of the dictionary is not correct"
    assert dic["Raw_data"]["Data"].shape == (512,), "FAIL - test_load_dat_file - PSD data shape is not correct"

def test_load_image():
    filepath = os.path.join(os.path.dirname(__file__), "test_data", "example_image.tif")

    dic = load_image_file(filepath)

    assert list(dic.keys()) == ["Raw_data", "Attributes"], "FAIL - test_load_dat_file - Structure of the dictionary is not correct"
    assert dic["Raw_data"]["Data"].shape == (512,512), "FAIL - test_load_tiff_file - data shape is not correct"
    dic_verif = {'FILEPROP.Name': 'example_image'}
    assert dic["Attributes"] == dic_verif, "FAIL - test_load_tiff_file - Attributes are not correct"

def test_load_npy_file():
    filepath = os.path.join(os.path.dirname(__file__), "test_data", "example_abscissa_GHOST.npy")
    dic = load_npy_file(filepath)

    assert list(dic.keys()) == ["Raw_data", "Attributes"], "FAIL - test_load_dat_file - Structure of the dictionary is not correct"
    assert dic["Raw_data"]["Data"].shape == (512,), "FAIL - test_load_tiff_file - data shape is not correct"
    dic_verif = {'FILEPROP.Name': 'example_abscissa_GHOST'}
    assert dic["Attributes"] == dic_verif, "FAIL - test_load_tiff_file - Attributes are not correct"

def test_load_sif_file():
    filepath = os.path.join(os.path.dirname(__file__), "test_data", "example_andor.sif")
    dic = load_sif_file(filepath)

    assert list(dic.keys()) == ["Raw_data", "Attributes"], "FAIL - test_load_dat_file - Structure of the dictionary is not correct"
    assert dic["Raw_data"]["Data"].shape == (1, 512, 512), "FAIL - test_load_tiff_file - data shape is not correct"
    assert dic["Attributes"]['SPECTROMETER.Detector_Model'] == "DU897_BV", "FAIL - test_load_sif_file - Detector attribute is not correct"
    
def test_load_general():
    filepath = os.listdir(os.path.join(os.path.dirname(__file__), "test_data"))

    for fp in filepath:
        _, ext = os.path.splitext(fp)
        if ext.lower() in [".dat"]:
            try: load_general(os.path.join(os.path.dirname(__file__), "test_data",fp))
            except LoadError_creator as e: pass
            
            try: load_general(os.path.join(os.path.dirname(__file__), "test_data",fp), creator = "TimeDomain")
            except LoadError_parameters as e: pass

        elif ext.lower() in [".tif", ".npy", "sif"]:
            dic = load_general(os.path.join(os.path.dirname(__file__), "test_data",fp))
            name = ".".join(os.path.basename(fp).split(".")[:-1])
            assert dic["Attributes"]['FILEPROP.Name'] == name

if __name__ == "__main__":
    test_load_dat_file()
    test_load_image()
    test_load_npy_file()
    test_load_sif_file()
    test_load_general()