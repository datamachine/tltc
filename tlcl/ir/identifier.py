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

    def is_bare(self):
        return self._ident.islower()

    def is_boxed(self):
        return not self.is_bare()

    def boxed(self):
        '''
        returns a copy of the identifier formatted as a boxed type
        '''
        ident = '{}{}'.format(self._ident[0].upper(), self._ident[1:])
        return IRIdentifier(self._kind, self._namespace, ident)

    def bare(self):
        '''
        returns a copy of the identifier formatted as a bare type
        '''
        ident = '{}{}'.format(self._ident[0].lower(), self._ident[1:])
        return IRIdentifier(self._kind, self._namespace, ident)

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
    def ident_full(self):
        fmt = '{ident}' if self.namespace is None else '{namespace}.{ident}'
        return fmt.format(namespace=self.namespace, ident=self.ident)

    def __str__(self):
        return self.ident_full

    def __repr__(self):
        fmt = '<IRIdentifier({}): kind={}, namespace={}, ident={}>'
        return fmt.format(self.ident_full, self.kind, self.namespace, self.ident)

    def __hash__(self):
        return hash(self.ident_full)
