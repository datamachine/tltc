from .identifier import TLIdentifer

class TLType:
    def __init__(self, namespace:TLNamespace, identifier:TLIdentifer):
        self.namespace = TLNamespace(namespace)
        self.identifier = TLIdentifer(identifier)
        self.ident_full = '{}.{}'.format(namespace, identifier) if namespace else identifier
