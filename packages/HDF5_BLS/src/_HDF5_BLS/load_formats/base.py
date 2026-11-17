import os
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np

from .load_errors import InvalidParameterError


@dataclass
class DatasetPayload:
    """Represents an individual array/dataset extracted from a source file."""
    data: np.ndarray
    dataset_type: str = "Raw_data"  # e.g., "Raw_data", "PSD", "Frequency", "Image", "Other"
    name: Optional[str] = None
    units: Optional[str] = None
    coordinates: Optional[Dict[str, np.ndarray]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Returns standard dictionary representation compatible with HDF5_BLS add_* methods."""
        res = {
            "Data": self.data,
            "Name": self.name or self.dataset_type,
            "Dataset_type": self.dataset_type,
        }
        if self.units:
            res["Units"] = self.units
        if self.coordinates:
            res["Coordinates"] = self.coordinates
        return res


@dataclass
class ImportPayload(Mapping):
    """
    Standard container returned by all loader plugins.
    Implements collections.abc.Mapping for 100% backward compatibility with legacy dict access:
    e.g., payload["Raw_data"]["Data"], payload["Attributes"], list(payload.keys()), etc.
    """
    datasets: Dict[str, DatasetPayload] = field(default_factory=dict)
    attributes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_dataset(
        self,
        name: str,
        data: np.ndarray,
        dataset_type: str = "Raw_data",
        units: Optional[str] = None,
        coordinates: Optional[Dict[str, np.ndarray]] = None
    ) -> DatasetPayload:
        payload = DatasetPayload(
            data=data,
            dataset_type=dataset_type,
            name=name,
            units=units,
            coordinates=coordinates
        )
        self.datasets[name] = payload
        return payload

    # --- Mapping (dict-like) Backward Compatibility ---
    def __getitem__(self, key: str) -> Any:
        if key == "Attributes":
            return self.attributes
        if key in self.datasets:
            return self.datasets[key].to_dict()
        # Fallback: check by dataset_type if key matches a type (e.g. "Raw_data" or "PSD")
        for d in self.datasets.values():
            if d.dataset_type == key:
                return d.to_dict()
        raise KeyError(f"Key '{key}' not found in ImportPayload datasets ({list(self.datasets.keys())}) or 'Attributes'")

    def __setitem__(self, key: str, value: Any) -> None:
        if key == "Attributes":
            if not isinstance(value, dict):
                raise ValueError("Attributes must be a dictionary")
            self.attributes = value
        elif isinstance(value, DatasetPayload):
            self.datasets[key] = value
        elif isinstance(value, dict) and "Data" in value:
            self.datasets[key] = DatasetPayload(
                data=value["Data"],
                name=value.get("Name", key),
                dataset_type=value.get("Dataset_type", key),
                units=value.get("Units"),
                coordinates=value.get("Coordinates"),
            )
        elif isinstance(value, np.ndarray):
            self.datasets[key] = DatasetPayload(data=value, name=key, dataset_type=key)
        else:
            self.metadata[key] = value

    def __iter__(self):
        keys = list(self.datasets.keys())
        if "Attributes" not in keys:
            keys.append("Attributes")
        return iter(keys)

    def __len__(self) -> int:
        return len(self.datasets) + (1 if "Attributes" not in self.datasets else 0)

    def __contains__(self, key: object) -> bool:
        if key == "Attributes":
            return True
        if key in self.datasets:
            return True
        for d in self.datasets.values():
            if d.dataset_type == key:
                return True
        return False

    def keys(self):
        return list(self.__iter__())

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def to_dict(self) -> Dict[str, Any]:
        """Convert entire payload to a plain Python dictionary."""
        d = {k: v.to_dict() for k, v in self.datasets.items()}
        d["Attributes"] = dict(self.attributes)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ImportPayload":
        """Construct an ImportPayload from a standard legacy dictionary."""
        payload = cls()
        for k, v in d.items():
            if k == "Attributes":
                payload.attributes = dict(v)
            elif isinstance(v, dict) and "Data" in v:
                payload.add_dataset(
                    name=k,
                    data=v["Data"],
                    dataset_type=v.get("Dataset_type", k),
                    units=v.get("Unit") or v.get("Units"),
                )
            elif isinstance(v, np.ndarray):
                payload.add_dataset(name=k, data=v, dataset_type=k)
            else:
                payload.metadata[k] = v
        return payload


@dataclass
class ParameterSpec:
    """Declarative specification for a format/loader parameter."""
    name: str
    type: Optional[type] = None  # e.g., int, float, str, bool, tuple, list
    default: Any = None
    required: bool = False
    description: str = ""
    choices: Optional[List[Any]] = None

    def validate(self, value: Any) -> Any:
        """Validates and coerces a parameter value against this specification."""
        if value is None:
            if self.required:
                raise InvalidParameterError(
                    f"Parameter '{self.name}' is required but was not provided.",
                    [self.name]
                )
            return self.default
        if self.choices is not None and value not in self.choices:
            raise InvalidParameterError(
                f"Parameter '{self.name}' must be one of {self.choices}, got '{value}'.",
                [self.name]
            )
        if self.type is not None and not isinstance(value, self.type):
            try:
                value = self.type(value)
            except Exception as e:
                raise InvalidParameterError(
                    f"Parameter '{self.name}' expected type {self.type.__name__}, got {type(value).__name__}: {e}",
                    [self.name]
                )
        return value


class BaseLoaderPlugin(ABC):
    """Abstract base class for all file loading plugins."""
    id: str = ""
    name: str = ""
    description: str = ""
    supported_extensions: List[str] = []
    creator_tag: Optional[str] = None
    parameter_specs: Dict[str, ParameterSpec] = {}

    def can_handle(self, filepath: str, creator: Optional[str] = None) -> bool:
        """
        Determines whether this plugin can handle the given file.
        Default checks extension and creator_tag.
        Subclasses can inspect file headers or magic bytes to disambiguate.
        """
        _, ext = os.path.splitext(filepath)
        if ext.lower() not in [e.lower() for e in self.supported_extensions]:
            return False
        if creator is not None:
            if self.creator_tag is not None:
                return creator.lower() == self.creator_tag.lower()
            return creator.lower() == self.id.lower()
        return True

    def validate_parameters(self, parameters: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validates supplied parameters against parameter_specs and applies defaults."""
        if not self.parameter_specs:
            return parameters

        params = parameters.copy() if parameters else {}
        validated = {}
        missing_required = []

        for name, spec in self.parameter_specs.items():
            if name not in params or params[name] is None:
                if spec.required:
                    missing_required.append(name)
                else:
                    validated[name] = spec.default
            else:
                validated[name] = spec.validate(params[name])

        if missing_required:
            raise InvalidParameterError(
                f"Plugin '{self.id}' is missing required parameters: {missing_required}",
                missing_required
            )

        # Preserve any additional unspec'd parameters passed
        for k, v in params.items():
            if k not in validated:
                validated[k] = v

        return validated

    @abstractmethod
    def load(
        self,
        filepath: str,
        parameters: Optional[Dict[str, Any]] = None,
        brillouin_type: Optional[str] = None
    ) -> ImportPayload:
        """Reads the source file and returns an ImportPayload."""
        pass
