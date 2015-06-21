from enum import Enum
import re

class IRType:
    _IRTypeKind = Enum('IRTypeKind', ['BOXED', 'BARE'])
    BOXED = _IRTypeKind.BOXED
    BARE = _IRTypeKind.BARE

    def __init__(self, identifier):
        if re.match('[a-z]', identifier.ident):
            self.kind = IRType.BARE
        else:
            self.kind = IRType.BOXED
        self.identifier = identifier
