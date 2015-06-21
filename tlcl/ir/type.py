from enum import Enum
import re

class IRType:
    _IRTypeKind = Enum('IRTypeKind', ['BOXED', 'BARE', 'NAT'])
    BOXED = _IRTypeKind.BOXED
    BARE = _IRTypeKind.BARE
    NAT = _IRTypeKind.NAT

    def __init__(self, identifier):
        if '#' == identifier.ident:
            self.kind = IRType.NAT
        elif re.match('[a-z]', identifier.ident):
            self.kind = IRType.BARE
        else:
            self.kind = IRType.BOXED
        self.identifier = identifier

    def __repr__(self):
        return '<IRType: kind={}, identifer={}>'.format(self.kind, self.identifier.full_ident)