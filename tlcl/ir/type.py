from enum import Enum

class IRType:
    _IRTypeKind = Enum('IRTypeKind', ['BOXED', 'BARE', 'NAT', 'TEMPLATE'])
    BOXED = _IRTypeKind.BOXED
    BARE = _IRTypeKind.BARE
    NAT = _IRTypeKind.NAT
    TEMPLATE = _IRTypeKind.TEMPLATE

    def __init__(self, kind, ir_ident):
        self._kind = kind
        self._ir_ident = ir_ident
        self.constructors = []
        self.functions = []

    @property
    def identifier(self):
        return self._ir_ident.identifier

    def __repr__(self):
        return '<IRType: kind={}, identifier={}>'.format(self._kind, self.identifier.full_ident)

    def __str__(self):
        return str(self.identifier)

    def __hash__(self):
        return hash(self.identifier)
