from enum import Enum


class IRIdentifier:
    _IdentifierKind = Enum('IdentifierKind', ['PARAMETER', 'COMBINATOR', 'TYPE'])
    PARAMETER = _IdentifierKind.PARAMETER
    COMBINATOR = _IdentifierKind.COMBINATOR
    TYPE = _IdentifierKind.TYPE

    def __init__(self, kind, namespace, ident):
        self.kind = IRIdentifier._IdentifierKind(kind)
        self.namespace = namespace
        self.ident = ident
        if namespace is None:
            self.full_ident = self.ident
        else:
            self.full_ident = '{}.{}'.format(namespace, ident)

    def __repr__(self):
        fmt = '<IRIdentifier: kind={}, namespace={}, ident={}, full_ident={}>'
        return fmt.format(self.kind, self.namespace, self.ident, self.full_ident)
