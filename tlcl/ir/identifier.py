
class IRIdentifier:
    def __init__(self, *, namespace=None, ident=None):
        self.namespace = namespace
        self.ident = ident
        if namespace is None:
            self.full_ident = '{ident}'.format(ident=ident)
        else:
            self.full_ident = '{namespace}.{ident}'.format(namespace=namespace, ident=ident)


if __name__ == '__main__':
    ident = TLIdentifier('myIdent')
    ns = NamespaceIdentifier('myNamespace')
    comb1 = CombinatorIdentifier('myNamespace', 'myIdent')
    comb2 = CombinatorIdentifier(ns, ident)

    print(ident)
    print(ns)
    print(comb1)
    print(comb2)