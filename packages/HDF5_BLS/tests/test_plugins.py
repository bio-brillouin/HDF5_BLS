import os
import tempfile
import pytest
import numpy as np

from HDF5_BLS.load_formats.base import (
    BaseLoaderPlugin,
    ImportPayload,
    DatasetPayload,
    ParameterSpec,
)
from HDF5_BLS.load_formats.registry import (
    LoaderRegistry,
    get_registry,
    register_loader,
    add_plugin_directory,
)
from HDF5_BLS.load_formats.load_errors import (
    LoadError,
    LoadError_creator,
    LoadError_parameters,
    PluginNotFoundError,
    AmbiguousPluginError,
    InvalidParameterError,
)
from HDF5_BLS.load_data import load_general
from HDF5_BLS import File, Wrapper


def test_import_payload_mapping():
    """Tests ImportPayload behaves both as an object and as a backwards-compatible dict."""
    payload = ImportPayload(attributes={"MEASURE.Sample": "Water"})
    data = np.arange(10)
    payload.add_dataset("Raw_data", data, dataset_type="Raw_data")

    # Dict-like access
    assert "Raw_data" in payload
    assert "Attributes" in payload
    assert np.array_equal(payload["Raw_data"]["Data"], data)
    assert payload["Attributes"]["MEASURE.Sample"] == "Water"
    assert list(payload.keys()) == ["Raw_data", "Attributes"]
    assert len(payload) == 2

    # Conversion
    d = payload.to_dict()
    assert isinstance(d, dict)
    assert "Raw_data" in d
    assert "Attributes" in d

    # Roundtrip from_dict
    payload2 = ImportPayload.from_dict(d)
    assert np.array_equal(payload2["Raw_data"]["Data"], data)
    assert payload2.attributes["MEASURE.Sample"] == "Water"


def test_custom_plugin_registration_and_loading(tmp_path):
    """Tests creating and registering a custom plugin."""
    class CustomBinPlugin(BaseLoaderPlugin):
        id = "custom_bin"
        name = "Custom Binary Loader"
        supported_extensions = [".custombin"]
        parameter_specs = {
            "scale": ParameterSpec(name="scale", type=float, default=1.0, description="Scaling factor"),
        }

        def load(self, filepath, parameters=None, brillouin_type=None):
            scale = (parameters or {}).get("scale", 1.0)
            data = np.ones((5, 5)) * scale
            payload = ImportPayload(attributes={"FILEPROP.Name": "test_custom"})
            payload.add_dataset("Raw_data", data)
            return payload

    registry = LoaderRegistry(auto_discover=False)
    plugin = CustomBinPlugin()
    registry.register(plugin)

    test_file = tmp_path / "sample.custombin"
    test_file.write_bytes(b"dummy content")

    payload = registry.load(str(test_file), parameters={"scale": 3.0})
    assert payload["Raw_data"]["Data"][0, 0] == 3.0
    assert payload["Attributes"]["FILEPROP.Name"] == "test_custom"


def test_parameter_spec_validation(tmp_path):
    """Tests parameter validation in BaseLoaderPlugin."""
    class StrictParamPlugin(BaseLoaderPlugin):
        id = "strict_param"
        supported_extensions = [".strict"]
        parameter_specs = {
            "required_int": ParameterSpec(name="required_int", type=int, required=True),
            "mode": ParameterSpec(name="mode", type=str, default="fast", choices=["fast", "accurate"]),
        }

        def load(self, filepath, parameters=None, brillouin_type=None):
            return ImportPayload()

    plugin = StrictParamPlugin()

    # Missing required parameter raises InvalidParameterError (and LoadError_parameters)
    with pytest.raises(InvalidParameterError) as exc_info:
        plugin.validate_parameters({})
    assert "required_int" in exc_info.value.parameters
    assert issubclass(InvalidParameterError, LoadError_parameters)

    # Invalid choice
    with pytest.raises(InvalidParameterError):
        plugin.validate_parameters({"required_int": 10, "mode": "invalid_mode"})

    # Valid
    validated = plugin.validate_parameters({"required_int": "42"})
    assert validated["required_int"] == 42
    assert validated["mode"] == "fast"


def test_ambiguity_and_creator_matching(tmp_path):
    """Tests conflict resolution when two plugins share an extension."""
    class PluginAlpha(BaseLoaderPlugin):
        id = "alpha"
        supported_extensions = [".multi"]
        creator_tag = "ALPHA"

        def can_handle(self, filepath, creator=None):
            if creator:
                return creator.lower() == "alpha"
            return False  # Cannot determine without creator

        def load(self, filepath, parameters=None, brillouin_type=None):
            p = ImportPayload(attributes={"creator": "alpha"})
            p.add_dataset("Raw_data", np.zeros(2))
            return p

    class PluginBeta(BaseLoaderPlugin):
        id = "beta"
        supported_extensions = [".multi"]
        creator_tag = "BETA"

        def can_handle(self, filepath, creator=None):
            if creator:
                return creator.lower() == "beta"
            return False

        def load(self, filepath, parameters=None, brillouin_type=None):
            p = ImportPayload(attributes={"creator": "beta"})
            p.add_dataset("Raw_data", np.ones(2))
            return p

    registry = LoaderRegistry(auto_discover=False)
    registry.register(PluginAlpha())
    registry.register(PluginBeta())

    test_file = tmp_path / "data.multi"
    test_file.write_text("sample")

    # Without creator -> raises AmbiguousPluginError (subclass of LoadError_creator)
    with pytest.raises(AmbiguousPluginError) as exc_info:
        registry.load(str(test_file))
    assert set(exc_info.value.creators) == {"ALPHA", "BETA"}
    assert issubclass(AmbiguousPluginError, LoadError_creator)

    # With creator ALPHA
    p_alpha = registry.load(str(test_file), creator="ALPHA")
    assert p_alpha["Attributes"]["creator"] == "alpha"

    # With creator BETA
    p_beta = registry.load(str(test_file), creator="BETA")
    assert p_beta["Attributes"]["creator"] == "beta"


def test_directory_discovery(tmp_path):
    """Tests dynamic discovery from a plugin directory."""
    plugin_code = '''
from HDF5_BLS.load_formats.base import BaseLoaderPlugin, ImportPayload
import numpy as np

class DiscoveredPlugin(BaseLoaderPlugin):
    id = "discovered_plugin"
    name = "Discovered Plugin"
    supported_extensions = [".dyn"]

    def load(self, filepath, parameters=None, brillouin_type=None):
        payload = ImportPayload(attributes={"discovered": True})
        payload.add_dataset("Raw_data", np.array([42]))
        return payload
'''
    plugin_file = tmp_path / "dyn_plugin.py"
    plugin_file.write_text(plugin_code)

    registry = LoaderRegistry(auto_discover=False)
    registry.discover_directory(str(tmp_path))

    assert "discovered_plugin" in registry._plugins
    test_dyn_file = tmp_path / "test.dyn"
    test_dyn_file.write_text("hello")
    res = registry.load(str(test_dyn_file))
    assert res["Attributes"]["discovered"] is True


def test_file_import_file_integration(tmp_path):
    """Tests File.import_file() ingestion into HDF5."""
    test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")
    npy_file = os.path.join(test_data_dir, "example_abscissa_GHOST.npy")
    dat_file = os.path.join(test_data_dir, "example_GHOST.DAT")

    h5_path = str(tmp_path / "test_import.h5")
    with File(h5_path, mode="w") as f:
        # Import NPY file
        f.import_file(npy_file, parent_group="Brillouin")
        assert "Raw_data" in f["Brillouin"]
        assert f["Brillouin"].attrs["FILEPROP.Name"] == "example_abscissa_GHOST"

        # Import GHOST DAT file
        f.create_group("Brillouin/Measure_GHOST")
        f.import_file(dat_file, parent_group="Brillouin/Measure_GHOST", creator="GHOST")
        assert "PSD" in f["Brillouin/Measure_GHOST"]
        assert "Frequency" in f["Brillouin/Measure_GHOST"]
        assert f["Brillouin/Measure_GHOST"].attrs["SPECTROMETER.Type"] == "TFP"


def test_wrapper_import_file_integration(tmp_path):
    """Tests Wrapper.import_file() ingestion into HDF5."""
    test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")
    npy_file = os.path.join(test_data_dir, "example_abscissa_GHOST.npy")

    h5_path = str(tmp_path / "test_wrapper_import.h5")
    wrp = Wrapper(filepath=h5_path)
    wrp.create_group("Measure", parent_group="Brillouin", Brillouin_type="Measure")
    wrp.import_file(npy_file, parent_group="Brillouin/Measure")
    assert "Raw_data" in wrp.get_children_elements("Brillouin/Measure")
    assert wrp.get_attributes("Brillouin/Measure")["FILEPROP.Name"] == "example_abscissa_GHOST"
    wrp.save = False
    wrp.close()
