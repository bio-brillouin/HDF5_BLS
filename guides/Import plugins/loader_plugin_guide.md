# Developing Loader Plugins for HDF5_BLS

The `HDF5_BLS` loading platform enables researchers, developers, and lab engineers to integrate arbitrary proprietary or open file formats seamlessly into `HDF5_BLS.File` and `HDF5_BLS.Wrapper`.

---

## 1. Minimal Plugin Example (15 Lines of Code)

To create a new loader, subclass `BaseLoaderPlugin` and implement the `load` method returning an `ImportPayload`:

```python
import numpy as np
from HDF5_BLS.load_formats.base import BaseLoaderPlugin, ImportPayload

class CustomCsvPlugin(BaseLoaderPlugin):
    id = "custom_csv_loader"
    name = "Custom CSV Loader"
    description = "Parses custom lab comma-separated spectra."
    supported_extensions = [".csv"]
    creator_tag = "MyLab"

    def load(self, filepath, parameters=None, brillouin_type=None):
        data = np.loadtxt(filepath, delimiter=",")
        payload = ImportPayload(attributes={"MEASURE.Sample": "Sample_A"})
        payload.add_dataset("Raw_data", data, dataset_type="Raw_data")
        return payload
```

---

## 2. Multi-Source Discovery: Distributing Your Plugin

`HDF5_BLS` automatically discovers plugins from multiple sources without needing to modify core codebase files:

### Method A: Drop-in User Directory (No Packaging Required)
Save your `.py` file into the user plugins directory:
- **Default path**: `~/.hdf5_bls/plugins/my_custom_loader.py`
- **Custom path via environment variable**: `export HDF5_BLS_PLUGIN_DIR=/shared/lab_plugins/`
- **Custom path via Python code**:
  ```python
  from HDF5_BLS.load_data import add_plugin_directory
  add_plugin_directory("/path/to/custom_plugins")
  ```

### Method B: Distribute via Pip Package (`entry_points`)
If publishing your loader as a reusable pip package, add the entry point in your package's `pyproject.toml`:

```toml
[project.entry-points."hdf5_bls.loaders"]
my_custom_loader = "my_package.loaders:CustomCsvPlugin"
```
Once installed with `pip install my-package`, `HDF5_BLS` detects and registers it automatically.

### Method C: Runtime Programmatic Registration
Register your plugin instance or class directly inside a script or Jupyter Notebook:

```python
from HDF5_BLS.load_data import register_loader
register_loader(CustomCsvPlugin())
```

---

## 3. Advanced Features

### 3.1. Format Sniffing & Conflict Disambiguation
If multiple plugins support the same extension (e.g. `.dat` or `.csv`), implement `can_handle()` to inspect file headers or magic bytes:

```python
class SmartCsvPlugin(BaseLoaderPlugin):
    id = "smart_csv"
    supported_extensions = [".csv"]

    def can_handle(self, filepath: str, creator: str = None) -> bool:
        if creator is not None:
            return creator.lower() == "smartcsv"
        # Sniff first line for signature header
        try:
            with open(filepath, "r") as f:
                header = f.readline()
                return "MyInstrumentSignature" in header
        except Exception:
            return False
```

If multiple candidates match and sniffing cannot disambiguate, `HDF5_BLS` raises an `AmbiguousPluginError` (which subclasses `LoadError_creator`), listing the candidates for the caller or GUI to select.

### 3.2. Declarative Parameters (`ParameterSpec`)
Declare format-specific parameters for validation and future auto-generated GUI forms:

```python
from HDF5_BLS.load_formats.base import BaseLoaderPlugin, ParameterSpec

class SifPlugin(BaseLoaderPlugin):
    id = "sif_loader"
    supported_extensions = [".sif"]
    parameter_specs = {
        "shape": ParameterSpec(
            name="shape",
            type=tuple,
            required=False,
            description="Target dimensions for reshaping raw array.",
        ),
        "grayscale": ParameterSpec(
            name="grayscale",
            type=bool,
            default=False,
            description="Convert color channels to grayscale.",
        ),
    }
```

---

## 4. Ingesting into HDF5

Use the unified `import_file()` method on `File` or `Wrapper` to load the file and persist all datasets and attributes into HDF5:

```python
from HDF5_BLS import File

with File("experiment.h5", mode="a") as f:
    f.import_file("my_data.custombin", parent_group="Brillouin/Measure_0", creator="MyLab")
```
