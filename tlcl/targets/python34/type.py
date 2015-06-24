from inspect import Signature, Parameter
from pathlib import Path
from collections import OrderedDict
from .ident import Python34Identifier

__all__ = ('Python34Type')

template="""
class {identifier}:
    def __init__(self):
        pass

    @staticmethod
    def deserialize(io_bytes):
        print('{identifier}')
        return io_bytes

"""

class Python34Type:
    def __init__(self, ident, ir_type):
        self._ident = ident
        self._ir_type = ir_type
        self._constructors = {}
        self._members = {}

    def add_constructor(self, constructor):
        self._constructors[constructor.number] = constructor
        for p in constructor.params:
            self._members[p.py3ident] = p

    @property
    def ident(self):
        return self._ident
    

    @property
    def py3ident(self):
        ident = self._ident.ir_ident.ident_full
        if ident == 'Vector t':
            ident = 'Vector'
        elif ident == '#':
            ident = 'NatNumber'
        else:
            ident = self._ident.py3ident
            ident = ident[0].upper() + ident[1:]

        ident = '{}'.format(ident)

        Python34Identifier.validate(ident)

        return ident

    def definition(self):
        init_sig = ', '.join(['self'] + ['{}=None'.format(m) for m in self._members])
        member_init = '\n        '.join(['self.{0} = {0}'.format(m) for m in self._members] or ['pass'])
        return template.format(identifier=self.py3ident, init_sig=init_sig, member_init=member_init)
