import pytest
import os
import pandas as pd
from _HDF5_BLS import NormalizedAttributes

def test_attributes_list():
    attrs = NormalizedAttributes.get_all()
    assert len(attrs) > 0
    
    # Check for a few key attributes
    names = [a.full_name for a in attrs]
    assert "MEASURE.Sample" in names
    assert "SPECTROMETER.Type" in names
    assert "FILEPROP.BLS_HDF5_Version" in names

def test_predefined_values():
    attrs = NormalizedAttributes.get_all()
    spec_type = next(a for a in attrs if a.full_name == "SPECTROMETER.Type")
    assert "1 stage VIPA" in spec_type.recommended_values
    assert "TFP" in spec_type.recommended_values

def test_to_pandas():
    df = NormalizedAttributes.to_pandas()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "Attribute" in df.columns
    assert "Units" in df.columns

def test_export_excel(tmp_path):
    excel_path = tmp_path / "attributes.xlsx"
    NormalizedAttributes.to_excel(str(excel_path))
    assert excel_path.exists()
    
    # Verify content
    df = pd.read_excel(excel_path)
    assert "MEASURE.Sample" in df["Attribute"].values

def test_export_csv(tmp_path):
    csv_path = tmp_path / "attributes.csv"
    NormalizedAttributes.to_csv(str(csv_path))
    assert csv_path.exists()
    
    # Verify content
    df = pd.read_csv(csv_path)
    assert "MEASURE.Sample" in df["Attribute"].values
