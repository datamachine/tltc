from inspect import Parameter
from .ident import Python34Identifier

class Python34Parameter:
    def __init__(self, ident, arg_type, ir_param):
        self._ident = ident
        self._arg_type = arg_type
        self._ir_param = ir_param

    @property
    def ir_param(self):
        return self._ir_param

    @property
    def py3ident(self):
        ident = self._ident.py3ident
        if ident == '#':
            ident = 'num'

        #Python34Identifier.validate(ident)
        return ident
    
    @property
    def arg_type(self):
        return self._arg_type

    def declaration(self):
        return self._identifier

    def definition(self):
        return self._identifier

    @property
    def parameter(self):
        return Parameter(self.identifier, Parameter.POSITIONAL_OR_KEYWORD)
