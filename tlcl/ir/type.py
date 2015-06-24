from enum import Enum

class IRType:
    _IRTypeKind = Enum('IRTypeKind', ['BOXED', 'BARE', 'NAT', 'TEMPLATE', 'VECTOR'])
    BOXED = _IRTypeKind.BOXED
    BARE = _IRTypeKind.BARE
    NAT = _IRTypeKind.NAT
    TEMPLATE = _IRTypeKind.TEMPLATE

    def __init__(self, kind, ir_ident, vector_type=None):
        self._kind = kind
        self._ir_ident = ir_ident
        self.constructors = []
        self.functions = []
        self._vector_type = vector_type

    @property
    def ident_full(self):
        return self._ir_ident.ident_full

    @property
    def ir_ident(self):
        return self._ir_ident

    def __repr__(self):
        return '<IRType: kind={}, identifier={}>'.format(self._kind, self.ident_full)

    def __str__(self):
        return str(self.ident_full)

    def __hash__(self):
        return hash(self.ident_full)
