from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

DEFAULT_GROUP_TYPE = "Root"
DEFAULT_DATASET_TYPE = "Other"

@dataclass(frozen=True)
class GroupType:
    """Metadata and specification for a Brillouin group type."""
    name: str
    description: str
    allowed_child_groups: List[str] = field(default_factory=list)


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


@dataclass(frozen=True)
class VersionConfig:
    """Specification for a specific version of HDF5_BLS."""
    version: str
    groups: Dict[str, GroupType]
    datasets: Dict[str, DatasetType]
    type_renames: Dict[str, str] = field(default_factory=dict)
    default_group_type: str = DEFAULT_GROUP_TYPE
    default_dataset_type: str = DEFAULT_DATASET_TYPE

    @property
    def group_names(self) -> List[str]:
        return list(self.groups.keys())

    @property
    def dataset_names(self) -> List[str]:
        return list(self.datasets.keys())

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
