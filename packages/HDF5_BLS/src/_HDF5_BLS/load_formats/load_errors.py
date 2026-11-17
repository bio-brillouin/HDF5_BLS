class LoadError(Exception):
    def __init__(self, msg) -> None:
        self.message = msg
        super().__init__(self.message)

class LoadError_creator(LoadError):
    def __init__(self, msg, creators) -> None:
        self.message = msg
        self.creators = creators
        super().__init__(self.message)

class LoadError_parameters(LoadError):
    def __init__(self, msg, parameters) -> None:
        self.message = msg
        self.parameters = parameters
        super().__init__(self.message)

class PluginNotFoundError(LoadError, ValueError):
    """Raised when no plugin supports the given file format or extension."""
    pass

class AmbiguousPluginError(LoadError_creator):
    """Raised when multiple plugins match a file and sniffing cannot disambiguate."""
    def __init__(self, msg, candidate_plugins) -> None:
        creators = []
        for p in candidate_plugins:
            tag = getattr(p, "creator_tag", None) or getattr(p, "id", str(p))
            if tag not in creators:
                creators.append(tag)
        super().__init__(msg, creators)
        self.candidate_plugins = candidate_plugins

class InvalidParameterError(LoadError_parameters):
    """Raised when required parameters are missing or invalid."""
    def __init__(self, msg, missing_or_invalid) -> None:
        if isinstance(missing_or_invalid, (list, tuple)):
            param_list = list(missing_or_invalid)
        elif isinstance(missing_or_invalid, dict):
            param_list = list(missing_or_invalid.keys())
        else:
            param_list = [str(missing_or_invalid)]
        super().__init__(msg, param_list)
        self.details = missing_or_invalid

class PluginExecutionError(LoadError):
    """Raised when a plugin fails internally during execution."""
    pass