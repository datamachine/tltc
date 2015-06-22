from enum import Enum
import re

class IRIdentifier:
    _IdentifierKind = Enum('IdentifierKind', ['PARAMETER', 'COMBINATOR', 'TYPE', 'TEMPLATE'])
    PARAMETER = _IdentifierKind.PARAMETER
    COMBINATOR = _IdentifierKind.COMBINATOR
    TYPE = _IdentifierKind.TYPE

    def __init__(self, kind, namespace, ident):
        self.kind = IRIdentifier._IdentifierKind(kind)
        self.namespace = namespace
        self.ident = ident

    def is_boxed(self):
        if self.kind is not IRIdentifier.TYPE:
            return False
        
        if self.ident in ['t']:
            return False

        return re.match('[a-z]', self.ident) is None

    @property
    def identifier(self):
        fmt = '{ident}' if self.namespace is None else '{namespace}.{ident}'
        return fmt.format(namespace=self.namespace, ident=self.ident)

    def __str__(self):
        return self.identifier

    def __repr__(self):
        fmt = '<IRIdentifier({}): kind={}, namespace={}, ident={}>'
        return fmt.format(self.identifier, self.kind, self.namespace, self.ident)

    def __hash__(self):
        return hash(str(self))
