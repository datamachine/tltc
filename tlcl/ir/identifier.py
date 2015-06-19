from enum import Enum


class IRIdentifier:
    _IdentifierKind = Enum('IdentifierKind', ['NAMESPACE', 'COMBINATOR', 'BOXED_TYPE', 'BARE_TYPE'])

    def __init__(self, *, namespace=None, ident=None):
        self.namespace = namespace
        self.ident = ident
        if namespace is None:
            self.full_ident = self.ident
        else:
            self.full_ident = '{}.{}'.format(namespace, ident)
