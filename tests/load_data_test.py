import pytest
import sys
import os
import datetime

sys.path.insert(0, "/Users/pierrebouvet/Documents/Code/HDF5_BLS_v1")
from HDF5_BLS.load_data import load_dat_file, load_tiff_file, load_general, load_npy_file, load_sif_file

def test_load_dat_file():
    filepath = os.path.join(os.path.dirname(__file__), "test_data", "example_GHOST.DAT")
    data, attributes = load_dat_file(filepath)

    dic_verif = {'FILEPROP.Name': 'example_GHOST', 'MEASURE.Sample': '', 'MEASURE.Date': '', 'SPECTROMETER.Scanning_Strategy': 'point_scanning', 'SPECTROMETER.Type': 'TFP', 'SPECTROMETER.Illumination_Type': 'CW', 'SPECTROMETER.Detector_Type': 'Photon Counter', 'SPECTROMETER.Filtering_Module': 'None', 'SPECTROMETER.Wavelength_nm': '532', 'SPECTROMETER.Scan_Amplitude': '20.1257', 'SPECTROMETER.Spectral_Resolution': '0.0393080078125'}

    assert attributes == dic_verif, "FAIL - test_load_dat_file - attributes are not correct"
    assert data.shape == (512,), "FAIL - test_load_dat_file - data shape is not correct"

def test_load_tiff_file():
    filepath = os.path.join(os.path.dirname(__file__), "test_data", "example_image.tif")

    data, attributes = load_tiff_file(filepath)

    dic_verif = {'FILEPROP.Name': 'example_image'}

    assert data.shape == (512,512), "FAIL - test_load_tiff_file - data shape is not correct"
    assert attributes == dic_verif, "FAIL - test_load_tiff_file - Attributes are not correct"

def test_load_npy_file():
    filepath = os.path.join(os.path.dirname(__file__), "test_data", "example_abscissa_GHOST.npy")
    data, attributes = load_npy_file(filepath)
    
    dic_verif = {'FILEPROP.Name': 'example_abscissa_GHOST'}

    assert data.shape == (512,), "FAIL - test_load_npy_file - data shape is not correct"
    assert attributes == dic_verif, "FAIL - test_load_npy_file - Attributes are not correct"

def test_load_sif_file():
    filepath = os.path.join(os.path.dirname(__file__), "test_data", "example_andor.sif")

    data, attributes = load_sif_file(filepath)
    
    assert data.shape == (512, 512), "FAIL - test_load_sif_file - data shape is not correct"
    assert attributes['SPECTROMETER.Detector_Model'] == "DU897_BV", "FAIL - test_load_sif_file - Detector attribute is not correct"
    assert attributes['MEASURE.Exposure_s'] == "0.00251", "FAIL - test_load_sif_file - Exposure attribute is not correct"


def test_load_general():
    filepath = os.listdir(os.path.join(os.path.dirname(__file__), "test_data"))

    for fp in filepath:
        _, ext = os.path.splitext(fp)
        if ext.lower() in [".dat", ".tif", ".npy", "sif"]:
            _, attributes = load_general(os.path.join(os.path.dirname(__file__), "test_data",fp))
            name = ".".join(os.path.basename(fp).split(".")[:-1])
            assert attributes['FILEPROP.Name'] == name
