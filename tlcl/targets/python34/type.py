from inspect import Signature, Parameter
from pathlib import Path
from collections import OrderedDict

__all__ = ('Python34Type')

template="""
class {identifier}:
    pass
"""

class Python34Type:
    def __init__(self, ident, ir_type):
        self._ident = ident
        self._ir_type = ir_type

    def definition(self, validate=True):
        if validate:
            self.validate()
        return template.format(**self.fields)

    @property
    def identifier(self):
        if str(self._ident.ir_ident) == '#':
            return 'Nat'
        if str(self._ident.ir_ident) == 'Vector t':
            return 'Vector'
        return self._ident

    def definition(self):
        return template.format(identifier=self.identifier)
