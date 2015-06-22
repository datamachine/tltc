from enum import Enum

class IRType:
    _IRTypeKind = Enum('IRTypeKind', ['BOXED', 'BARE', 'NAT'])
    BOXED = _IRTypeKind.BOXED
    BARE = _IRTypeKind.BARE
    NAT = _IRTypeKind.NAT

    def __init__(self, identifier):
        if identifier.is_boxed():
            self.kind = IRType.BOXED
        else:
            self.kind = IRType.BARE

        self.identifier = identifier
        self.constructors = []
        self.functions = []

    def __repr__(self):
        return '<IRType: kind={}, identifier={}>'.format(self.kind, self.identifier.full_ident)

    def __str__(self):
        return str(self.identifier)