import pytest
import tempfile
import os
import shutil
import h5py
import numpy as np

from HDF5_BLS import (
    get_config,
    VersionConfig,
    GroupType,
    DatasetType,
    Wrapper,
    Wrapper_file,
)
from HDF5_BLS.wrapper import HDF5_BLS_Version


@pytest.fixture
def temp_dir():
    dirpath = tempfile.mkdtemp()
    yield dirpath
    if os.path.exists(dirpath):
        shutil.rmtree(dirpath)


def test_get_config_defaults_and_fallback():
    cfg_none = get_config()
    assert cfg_none is not None
    assert cfg_none.version == "1.0"

    cfg_empty = get_config("")
    assert cfg_empty.version == "1.0"

    cfg_exact = get_config("1.0")
    assert cfg_exact.version == "1.0"

    # If an unregistered/unknown version is requested, fallback to latest
    cfg_unknown = get_config("99.9")
    assert cfg_unknown.version == "1.0"


def test_default_types_for_untyped_elements():
    cfg = get_config("1.0")

    # Untyped or unknown datasets default to "Other"
    ds_none = cfg.get_dataset(None)
    assert ds_none is not None
    assert ds_none.name == "Other"

    ds_empty = cfg.get_dataset("")
    assert ds_empty.name == "Other"

    ds_unknown = cfg.get_dataset("CompletelyUnknownDatasetType")
    assert ds_unknown.name == "Other"

    # Untyped or unknown groups default to "Root"
    grp_none = cfg.get_group(None)
    assert grp_none is not None
    assert grp_none.name == "Root"

    grp_empty = cfg.get_group("")
    assert grp_empty.name == "Root"

    grp_unknown = cfg.get_group("CompletelyUnknownGroupType")
    assert grp_unknown.name == "Root"


def test_alias_and_prefix_resolution():
    cfg = get_config("1.0")

    # Historical alias resolution: Shift_std -> Shift_err
    ds_shift_std = cfg.get_dataset("Shift_std")
    assert ds_shift_std.name == "Shift_err"
    assert ds_shift_std.default_unit == "GHz"

    ds_lw_std = cfg.get_dataset("Linewidth_std")
    assert ds_lw_std.name == "Linewidth_err"

    # Abscissa dimension prefix resolution
    ds_abscissa = cfg.get_dataset("Abscissa_0_1")
    assert ds_abscissa.name == "Abscissa"


def test_allowed_parent_groups_and_validation():
    cfg = get_config("1.0")

    # Shift is only allowed in Treatment
    assert cfg.validate_dataset_parent("Shift", "Treatment") is True
    assert cfg.validate_dataset_parent("Shift", "Measure") is False
    assert cfg.validate_dataset_parent("Shift", "Root") is False

    # Raw_data is allowed in Measure, Calibration_spectrum, Impulse_response
    assert cfg.validate_dataset_parent("Raw_data", "Measure") is True
    assert cfg.validate_dataset_parent("Raw_data", "Calibration_spectrum") is True
    assert cfg.validate_dataset_parent("Raw_data", "Treatment") is False

    # Other is allowed in Measure, Treatment, Root, etc.
    assert cfg.validate_dataset_parent("Other", "Measure") is True
    assert cfg.validate_dataset_parent("Other", "Treatment") is True
    assert cfg.validate_dataset_parent("Other", "Root") is True

    # Untyped dataset and parent group fallback
    assert cfg.validate_dataset_parent(None, None) is True


def test_get_type_description():
    cfg = get_config("1.0")

    desc_raw = cfg.get_type_description("Raw_data")
    assert desc_raw is not None
    assert "scattered light" in desc_raw

    desc_grp = cfg.get_type_description("Measure")
    assert desc_grp is not None
    assert "main group" in desc_grp

    desc_alias = cfg.get_type_description("Shift_std")
    assert desc_alias is not None
    assert "standard error" in desc_alias

    assert cfg.get_type_description("NonExistentType") is None
    assert cfg.get_type_description(None) is None


def test_to_dict_serialization():
    cfg = get_config("1.0")
    d = cfg.to_dict()

    assert d["version"] == "1.0"
    assert d["default_group_type"] == "Root"
    assert d["default_dataset_type"] == "Other"
    assert "Measure" in d["groups"]
    assert "Raw_data" in d["datasets"]
    assert d["datasets"]["Raw_data"]["allowed_parent_groups"] == ["Measure", "Calibration_spectrum", "Impulse_response"]


def test_wrapper_file_version_inference(temp_dir):
    # Test 1: File created without HDF5_BLS_version attribute assumes latest version
    legacy_file = os.path.join(temp_dir, "legacy.h5")
    with h5py.File(legacy_file, 'w') as f:
        grp = f.create_group("Brillouin")
        grp.attrs["Brillouin_type"] = "Root"
        # Notice: No HDF5_BLS_version attribute

    # Opening with Wrapper
    wrp = Wrapper(legacy_file)
    assert wrp.config.version == "1.0"

    # Opening with Wrapper_file
    with Wrapper_file(legacy_file) as wf:
        assert wf.config.version == "1.0"
        assert wf.get_type_description("Raw_data") is not None
        assert wf.get_allowed_parent_groups("Shift") == ["Treatment"]


def test_wrapper_explicit_version(temp_dir):
    new_file = os.path.join(temp_dir, "versioned.h5")
    with Wrapper_file(new_file, version="1.0") as wf:
        assert wf.config.version == "1.0"
        assert wf["Brillouin"].attrs["HDF5_BLS_version"] == "1.0"
