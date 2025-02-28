class LoadError_creator(Exception):
    def __init__(self, msg, creators) -> None:
        self.message = msg
        self.creators = creators
        super().__init__(self.message)

class LoadError_parameters(Exception):
    def __init__(self, msg, parameters) -> None:
        self.message = msg
        self.parameters = parameters
        super().__init__(self.message)