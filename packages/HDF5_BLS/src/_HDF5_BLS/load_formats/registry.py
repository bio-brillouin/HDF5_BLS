import os
import sys
import glob
import logging
import importlib
import importlib.util
from typing import Any, Dict, List, Optional, Type, Union

from .base import BaseLoaderPlugin, ImportPayload
from .load_errors import (
    LoadError,
    LoadError_creator,
    PluginNotFoundError,
    AmbiguousPluginError,
    PluginExecutionError,
)

logger = logging.getLogger(__name__)

DEFAULT_USER_PLUGIN_DIR = os.path.expanduser("~/.hdf5_bls/plugins")


class LoaderRegistry:
    """
    Central registry for discovering, resolving, and invoking file loader plugins.
    Supports multi-source discovery:
    1. Built-in loaders (Ghost, TimeDomain, Npy, Sif, Image)
    2. Standard Python entry_points ("hdf5_bls.loaders")
    3. User plugin directory (~/.hdf5_bls/plugins or $HDF5_BLS_PLUGIN_DIR)
    4. Programmatic registration
    """

    def __init__(self, auto_discover: bool = True):
        self._plugins: Dict[str, BaseLoaderPlugin] = {}
        self._discovered: bool = False
        if auto_discover:
            self.discover_all()

    def register(self, plugin: Union[BaseLoaderPlugin, Type[BaseLoaderPlugin]], override: bool = False) -> None:
        """Registers a plugin instance or class."""
        if isinstance(plugin, type) and issubclass(plugin, BaseLoaderPlugin):
            plugin = plugin()

        if not isinstance(plugin, BaseLoaderPlugin):
            raise TypeError(f"Expected BaseLoaderPlugin instance or subclass, got {type(plugin)}")

        if not plugin.id:
            raise ValueError(f"Plugin {plugin} must have a non-empty 'id' attribute.")

        if plugin.id in self._plugins and not override:
            logger.debug(f"Plugin '{plugin.id}' is already registered. Skipping.")
            return

        self._plugins[plugin.id] = plugin
        logger.debug(f"Registered loader plugin '{plugin.id}' for extensions {plugin.supported_extensions}")

    def unregister(self, plugin_id: str) -> Optional[BaseLoaderPlugin]:
        """Removes a registered plugin by ID."""
        return self._plugins.pop(plugin_id, None)

    def get_plugin(self, plugin_id: str) -> Optional[BaseLoaderPlugin]:
        """Retrieves a registered plugin by ID."""
        return self._plugins.get(plugin_id)

    def list_plugins(self) -> List[BaseLoaderPlugin]:
        """Returns all registered plugins."""
        return list(self._plugins.values())

    def discover_builtins(self) -> None:
        """Discovers and registers built-in plugins defined in load_formats."""
        try:
            from .load_dat import GhostDatPlugin, TimeDomainDatPlugin
            from .load_npy import NpyPlugin
            from .load_sif import SifPlugin
            from .load_image import ImagePlugin

            self.register(GhostDatPlugin())
            self.register(TimeDomainDatPlugin())
            self.register(NpyPlugin())
            self.register(SifPlugin())
            self.register(ImagePlugin())
        except ImportError as e:
            logger.warning(f"Could not import all built-in loader plugins: {e}")

    def discover_entry_points(self) -> None:
        """Discovers loader plugins via Python entry points ('hdf5_bls.loaders')."""
        try:
            if sys.version_info >= (3, 10):
                from importlib.metadata import entry_points
                eps = entry_points(group="hdf5_bls.loaders")
            else:
                import pkg_resources
                eps = [ep for ep in pkg_resources.iter_entry_points(group="hdf5_bls.loaders")]

            for ep in eps:
                try:
                    plugin_cls = ep.load()
                    self.register(plugin_cls)
                except Exception as e:
                    logger.warning(f"Failed to load entry_point '{ep.name}': {e}")
        except Exception as e:
            logger.debug(f"Entry points discovery skipped or encountered an error: {e}")

    def discover_directory(self, dir_path: str) -> None:
        """Scans a directory for .py files and registers any BaseLoaderPlugin classes found."""
        if not os.path.isdir(dir_path):
            return

        for py_file in glob.glob(os.path.join(dir_path, "*.py")):
            module_name = f"_hdf5_bls_user_plugin_{os.path.splitext(os.path.basename(py_file))[0]}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    # Inspect module attributes for BaseLoaderPlugin subclasses
                    for attr_name in dir(mod):
                        attr = getattr(mod, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, BaseLoaderPlugin)
                            and attr is not BaseLoaderPlugin
                        ):
                            self.register(attr())
                        elif isinstance(attr, BaseLoaderPlugin):
                            self.register(attr)
            except Exception as e:
                logger.warning(f"Failed loading plugin file '{py_file}': {e}")

    def discover_user_plugins(self) -> None:
        """Discovers plugins from user directory or HDF5_BLS_PLUGIN_DIR environment variable."""
        user_dir = os.environ.get("HDF5_BLS_PLUGIN_DIR", DEFAULT_USER_PLUGIN_DIR)
        self.discover_directory(user_dir)

    def discover_all(self) -> None:
        """Runs discovery across all sources."""
        if self._discovered:
            return
        self.discover_builtins()
        self.discover_entry_points()
        self.discover_user_plugins()
        self._discovered = True

    def resolve_loader(self, filepath: str, creator: Optional[str] = None) -> BaseLoaderPlugin:
        """
        Resolves the appropriate BaseLoaderPlugin for a given file and optional creator.
        Implements multi-stage resolution:
        1. Extension matching
        2. Explicit creator match if provided
        3. Header / content sniffing via can_handle()
        4. Ambiguity / error raising with backward-compatible exceptions
        """
        _, ext = os.path.splitext(filepath)
        ext = ext.lower()

        matching_plugins = [
            p for p in self._plugins.values()
            if ext in [e.lower() for e in p.supported_extensions]
        ]

        if not matching_plugins:
            raise PluginNotFoundError(f"Unsupported file format: {ext}")

        # If creator is explicitly provided, match by creator_tag or plugin id
        if creator is not None:
            for p in matching_plugins:
                if (p.creator_tag and p.creator_tag.lower() == creator.lower()) or p.id.lower() == creator.lower():
                    return p
            creators_list = [p.creator_tag or p.id for p in matching_plugins]
            raise LoadError_creator(
                f"Unsupported creator {creator}, accepted values are: {', '.join(creators_list)}",
                creators_list
            )

        # Sniff candidate plugins using can_handle
        confident_matches = []
        for p in matching_plugins:
            try:
                if p.can_handle(filepath, creator=creator):
                    confident_matches.append(p)
            except Exception:
                pass

        if len(confident_matches) == 1:
            return confident_matches[0]

        # If still ambiguous or multiple match
        candidates = confident_matches if confident_matches else matching_plugins
        raise AmbiguousPluginError(
            f"Multiple creators found for extension '{ext}'. Please select one: {[p.creator_tag or p.id for p in candidates]}",
            candidates
        )

    def load(
        self,
        filepath: str,
        creator: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        brillouin_type: Optional[str] = None
    ) -> ImportPayload:
        """
        Resolves plugin, validates parameters, and loads file into an ImportPayload.
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"The file '{filepath}' does not exist.")

        plugin = self.resolve_loader(filepath, creator=creator)
        validated_params = plugin.validate_parameters(parameters)

        try:
            return plugin.load(filepath, parameters=validated_params, brillouin_type=brillouin_type)
        except (LoadError, FileNotFoundError, ValueError):
            raise
        except Exception as e:
            raise PluginExecutionError(f"Error loading '{filepath}' with plugin '{plugin.id}': {e}") from e


# Global default registry instance
default_registry = LoaderRegistry(auto_discover=False)


def get_registry() -> LoaderRegistry:
    """Returns the default loader registry, initializing discovery if needed."""
    if not default_registry._discovered:
        default_registry.discover_all()
    return default_registry


def register_loader(plugin: Union[BaseLoaderPlugin, Type[BaseLoaderPlugin]]) -> None:
    """Programmatically registers a loader plugin with the default registry."""
    get_registry().register(plugin)


def add_plugin_directory(dir_path: str) -> None:
    """Scans and registers plugins from an additional directory."""
    get_registry().discover_directory(dir_path)
