
class WrapperError(Exception):
    """Base class for all the exceptions raised by the Wrapper class.
    """
    def __init__(self, msg) -> None:
        self.message = msg
        super().__init__(self.message)

class WrapperError_FileNotFound(WrapperError):
    """Error raised when a file does not exist.
    """
    def __init__(self, msg) -> None:
        self.message = msg
        super().__init__(self.message)

class WrapperError_StructureError(WrapperError):
    """Error raised when the expected structure of the file is not correct.
    """
    def __init__(self, msg) -> None:
        self.message = msg
        super().__init__(self.message)

class WrapperError_Overwrite(WrapperError):
    """Error raised when an element is to be overwritten.
    """
    def __init__(self, msg) -> None:
        self.message = msg
        super().__init__(self.message)

class WrapperError_ArgumentType(WrapperError):
    """Error raised when an argument is of the wrong type.
    """
    def __init__(self, msg) -> None:
        self.message = msg
        super().__init__(self.message)

class WrapperError_Save(WrapperError):
    """Error raised when teh file is not saved or cannot be saved.
    """
    def __init__(self, msg) -> None:
        self.message = msg
        super().__init__(self.message)
