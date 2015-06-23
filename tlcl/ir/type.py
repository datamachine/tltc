from enum import Enum

class IRType:
    _IRTypeKind = Enum('IRTypeKind', ['BOXED', 'BARE', 'NAT'])
    BOXED = _IRTypeKind.BOXED
    BARE = _IRTypeKind.BARE
    NAT = _IRTypeKind.NAT

    def __init__(self, ir_ident):
        if ir_ident.is_boxed():
            self.kind = IRType.BOXED
        else:
            self.kind = IRType.BARE

        self._ir_ident = ir_ident
        self.constructors = []
        self.functions = []

    @property
    def identifier(self):
        return self._ir_ident.identifier

    def __repr__(self):
        return '<IRType: kind={}, identifier={}>'.format(self.kind, self.identifier.full_ident)

    def __str__(self):
        return str(self.identifier)

    def __hash__(self):
        return hash(self.identifier)
