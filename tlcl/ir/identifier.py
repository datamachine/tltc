from enum import Enum
import re

class IRIdentifier:
    _IdentifierKind = Enum('IdentifierKind', ['PARAMETER', 'COMBINATOR', 'TYPE', 'TEMPLATE'])
    PARAMETER = _IdentifierKind.PARAMETER
    COMBINATOR = _IdentifierKind.COMBINATOR
    TYPE = _IdentifierKind.TYPE
    TEMPLATE = _IdentifierKind.TEMPLATE

    def __init__(self, kind, namespace, ident):
        self._kind = IRIdentifier._IdentifierKind(kind)
        self._namespace = namespace
        self._ident = ident

    def is_boxed(self):
        if self.kind is not IRIdentifier.TYPE:
            return False
        
        if self.ident in ['t']:
            return False

        return re.match('[a-z]', self.ident) is None

    @property
    def kind(self):
        return self._kind

    @property
    def namespace(self):
        return self._namespace

    @property
    def ident(self):
        return self._ident      

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
        return hash(self.identifier)
