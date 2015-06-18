from .tlobject import TLObject

class TLIdentifier(TLObject):
    def __str__(self):
        return self.identifier

class NamespaceIdentifier(TLIdentifier):
    pass

class CombinatorIdentifier(TLObject):
    _combinators = []

    __slots__ = ('namespace', 'identifier')

    def __new__(cls, namespace, identifier):
        result = super(CombinatorIdentifier, cls).__new__(cls)
        result.namespace = NamespaceIdentifier(namespace)
        result.identifier = TLIdentifier(identifier)
        # Combinator identifiers must be unique
        if result in CombinatorIdentifier._combinators:
            raise SyntaxError('Combinator already defined: {}'.format(CombinatorIdentifier._combinators))

        return result

    def __init__(self, namespace, identifier):
        pass

    def __str__(self):
        return '{}.{}'.format(self.namespace, self.identifier)

if __name__ == '__main__':
    ident = TLIdentifier('myIdent')
    ns = NamespaceIdentifier('myNamespace')
    comb1 = CombinatorIdentifier('myNamespace', 'myIdent')
    comb2 = CombinatorIdentifier(ns, ident)

    print(ident)
    print(ns)
    print(comb1)
    print(comb2)