from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Any
import re
import pkgutil
import importlib
import pandas as pd
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

DEFAULT_GROUP_TYPE = "Root"
DEFAULT_DATASET_TYPE = "Other"

# Groups in H5 file
@dataclass(frozen=True)
class GroupType:
    """Metadata and specification for a Brillouin group type."""
    name: str
    description: str
    allowed_child_groups: List[str] = field(default_factory=list)

# Datasets in H5 file
@dataclass(frozen=True)
class DatasetType:
    """Metadata and specification for a Brillouin dataset type."""
    name: str
    description: str
    allowed_parent_groups: List[str] = field(default_factory=list)
    default_unit: Optional[str] = None
    expected_ndim: Optional[List[int]] = None

    def is_allowed_in(self, parent_group_type: str) -> bool:
        """Check if this dataset can be placed in a group with the given Brillouin type."""
        # If allowed_parent_groups is empty, it can be stored in any group
        if not self.allowed_parent_groups:
            return True
        return parent_group_type in self.allowed_parent_groups

# Attributes in H5 file
@dataclass(frozen=True)
class Attribute:
    """
    Metadata for a standardized HDF5 attribute.
    """
    group: str
    name: str
    units: Optional[str] = None
    description: Optional[str] = None
    example: Any = None
    recommended_values: List[Any] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.group}.{self.name}"

# Version configurator (stores the spec for each version)
@dataclass(frozen=True)
class VersionConfig:
    """Specification for a specific version of HDF5_BLS."""
    version: str
    groups: Dict[str, GroupType]
    datasets: Dict[str, DatasetType]
    attributes: Dict[str, Attribute]
    type_renames: Dict[str, str] = field(default_factory=dict)
    default_group_type: str = DEFAULT_GROUP_TYPE
    default_dataset_type: str = DEFAULT_DATASET_TYPE

    @property
    def attribute_names(self) -> List[str]:
        return list(self.attributes.keys())
    
    @property
    def dataset_names(self) -> List[str]:
        return list(self.datasets.keys())
    @property
    def group_names(self) -> List[str]:
        return list(self.groups.keys())

    def get_attribute(self, name: str) -> Optional[Attribute]:
        """Retrieves an Attribute by full_name ('MEASURE.Sample') or simple name ('Sample')."""
        if name in self.attributes:
            return self.attributes[name]
        for attr in self.attributes.values():
            if attr.name == name:
                return attr
        return None

    def get_all_attributes(self) -> List[Attribute]:
        """Returns list of all normalized attributes for this version."""
        return list(self.attributes.values())

    def get_attribute_groups(self) -> List[str]:
        """Returns sorted list of attribute meta-groups (e.g. 'FILEPROP', 'MEASURE', 'SPECTROMETER')."""
        return sorted(list(set(attr.group for attr in self.attributes.values())))
    
    def get_attributes_by_group(self, group: str) -> List[Attribute]:
        """Returns attributes belonging to a specific meta-group (e.g. 'FILEPROP', 'MEASURE', 'SPECTROMETER')."""
        return [attr for attr in self.attributes.values() if attr.group == group]

    def get_dataset(self, name: Optional[str] = None) -> Optional[DatasetType]:
        """Retrieves DatasetType by name, resolving aliases/renames and Abscissa prefixes.
        Defaults to 'Other' if name is empty, None, or unrecognized."""
        if not name:
            return self.datasets.get(self.default_dataset_type)
        canonical_name = self.type_renames.get(name, name)
        if canonical_name.startswith("Abscissa"):
            base_name = "Abscissa"
        else:
            base_name = canonical_name
        return self.datasets.get(base_name, self.datasets.get(self.default_dataset_type))

    def get_group(self, name: Optional[str] = None) -> Optional[GroupType]:
        """Retrieves GroupType by name, resolving aliases/renames.
        Defaults to 'Root' if name is empty, None, or unrecognized."""
        if not name:
            return self.groups.get(self.default_group_type)
        canonical_name = self.type_renames.get(name, name)
        return self.groups.get(canonical_name, self.groups.get(self.default_group_type))

    def get_type_description(self, type_name: Optional[str]) -> Optional[str]:
        """Returns the description of a dataset or group type, or None if unknown."""
        if not type_name:
            return None
        canonical = self.get_canonical_type_name(type_name)
        if canonical.startswith("Abscissa"):
            canonical = "Abscissa"
        if canonical in self.datasets:
            return self.datasets[canonical].description
        if canonical in self.groups:
            return self.groups[canonical].description
        return None

    def validate_dataset_parent(self, dataset_type: Optional[str], parent_group_type: Optional[str]) -> bool:
        """Validates whether a dataset of dataset_type can be stored in parent_group_type."""
        ds = self.get_dataset(dataset_type)
        grp = self.get_group(parent_group_type)
        parent_canonical = grp.name if grp else self.default_group_type
        if ds is not None:
            return ds.is_allowed_in(parent_canonical)
        return True

    def get_canonical_type_name(self, name: str) -> str:
        """Resolves historical or alias names to the canonical name in this version."""
        return self.type_renames.get(name, name)

    def to_dict(self) -> Dict[str, Any]:
        """Exports configuration as a serializable dictionary."""
        return {
            "version": self.version,
            "default_group_type": self.default_group_type,
            "default_dataset_type": self.default_dataset_type,
            "groups": {
                k: {
                    "name": v.name,
                    "description": v.description,
                    "allowed_child_groups": v.allowed_child_groups,
                }
                for k, v in self.groups.items()
            },
            "datasets": {
                k: {
                    "name": v.name,
                    "description": v.description,
                    "allowed_parent_groups": v.allowed_parent_groups,
                    "default_unit": v.default_unit,
                    "expected_ndim": v.expected_ndim,
                }
                for k, v in self.datasets.items()
            },
            "type_renames": self.type_renames,
        }

    def attributes_to_pandas(self) -> "pd.DataFrame":
        """
        Returns a pandas DataFrame representation of the normalized attributes.
        """
        data = []
        current_group = None
        for attr in self.attributes.values():
            if attr.group != current_group:
                data.append({
                    "Attribute": attr.group,
                    "Value": None,
                    "Units": None,
                    "Norm or precisions on parameter": None,
                    "Example": None,
                    "Recommended Values": None
                })
                current_group = attr.group
            
            data.append({
                "Attribute": attr.full_name,
                "Value": None,
                "Units": attr.units,
                "Norm or precisions on parameter": attr.description,
                "Example": attr.example,
                "Recommended Values": ", ".join(map(str, attr.recommended_values)) if attr.recommended_values else None
            })
            
        return pd.DataFrame(data)

    def attributes_to_excel(self, path: str):
        """Generates an Excel spreadsheet of the normalized attributes with dropdowns."""
        df = self.attributes_to_pandas()
        
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Attributes')
            workbook = writer.book
            worksheet = writer.sheets['Attributes']

            # Find columns
            attribute_col = 1 # A
            value_col = 2     # B
            
            # Add data validation for attributes with recommended values
            # Rows are 2-indexed (1 is header)
            row_idx = 2
            current_group = None
            for attr in self.attributes.values():
                if attr.group != current_group:
                    row_idx += 1 # Skip group header row
                    current_group = attr.group
                
                if attr.recommended_values:
                    dv = DataValidation(
                        type="list", 
                        formula1=f'"{",".join(map(str, attr.recommended_values))}"',
                        allow_blank=True
                    )
                    dv.add(f"{get_column_letter(value_col)}{row_idx}")
                    worksheet.add_data_validation(dv)
                
                row_idx += 1

    def attributes_to_csv(self, path: str):
        """Generates a CSV file of the normalized attributes."""
        df = self.attributes_to_pandas()
        df.to_csv(path, index=False)


# Global registry of version configurations -> key are string, values are VersionConfig 
REGISTERED_VERSIONS: Dict[str, VersionConfig] = {}

def _parse_version_key(version_str: str) -> Tuple[Any, ...]:
    """Helper to sort versions numerically (e.g. '1.10' > '1.2')."""
    parts = re.split(r'[-_.]', str(version_str).strip())
    return tuple((0, int(p)) if p.isdigit() else (1, p) for p in parts)

def _load_available_versions() -> None:
    """Automatically scans the 'versions' package and registers all VersionConfig instances."""
    if REGISTERED_VERSIONS:
        return
    from . import versions as versions_pkg
    # Discover and import all modules inside the versions package
    for _, modname, _ in pkgutil.iter_modules(versions_pkg.__path__):
        if modname.startswith("_"):
            continue
        module = importlib.import_module(f".versions.{modname}", package=__package__)
        for obj in vars(module).values():
            if isinstance(obj, VersionConfig):
                register_version(obj)

def get_available_versions() -> List[str]:
    """Returns a sorted list of all available versions (e.g. ['1.0', '1.1'])."""
    _load_available_versions()
    return sorted(REGISTERED_VERSIONS.keys(), key=_parse_version_key)

def get_latest_version() -> str:
    """Returns the latest available version string (e.g. '1.0')."""
    versions = get_available_versions()
    if not versions:
        raise RuntimeError("No HDF5_BLS versions registered or found in 'versions/' directory.")
    return versions[-1]

def register_version(config: VersionConfig) -> None:
    """Registers a VersionConfig in the global registry."""
    REGISTERED_VERSIONS[config.version] = config

def get_config(version: Optional[str] = None) -> VersionConfig:
    """Retrieves the VersionConfig for the requested version string.
    If version is None, empty, or not found, defaults to the latest registered version.
    """
    _load_available_versions()
    if version is None or str(version).strip() == "":
        return REGISTERED_VERSIONS[get_latest_version()]
    version_str = str(version).strip()
    if version_str in REGISTERED_VERSIONS:
        return REGISTERED_VERSIONS[version_str]
    # Fallback to latest registered version if unknown version is requested
    return REGISTERED_VERSIONS[get_latest_version()]
