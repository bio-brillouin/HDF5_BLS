class WrapperError(Exception):
    def __init__(self, msg) -> None:
        self.message = msg
        super().__init__(self.message)

class WrapperError_FileNotFound(Exception):
    def __init__(self, msg) -> None:
        self.message = msg
        super().__init__(self.message)

class WrapperError_StructureError(Exception):
    def __init__(self, msg) -> None:
        self.message = msg
        super().__init__(self.message)

class WrapperError_Overwrite(Exception):
    def __init__(self, msg) -> None:
        self.message = msg
        super().__init__(self.message)

class WrapperError_ArgumentType(Exception):
    def __init__(self, msg) -> None:
        self.message = msg
        super().__init__(self.message)

class WrapperError_Save(Exception):
    def __init__(self, msg) -> None:
        self.message = msg
        super().__init__(self.message)
