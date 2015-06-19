from enum import Enum

class IRType:
    _IRTypeKind = Enum('IRTypeKind', ['BOXED', 'BARE'])

    def __init__(self, identifier):
        self.identifier = identifier
