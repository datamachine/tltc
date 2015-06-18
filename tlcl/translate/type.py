from .identifier import TLIdentifier

class TLType:
    def __init__(self, namespace, identifier):
        self.namespace = str(namespace)
        self.identifier = str(identifier)
        self.ident_full = '{}.{}'.format(namespace, identifier) if namespace else identifier
