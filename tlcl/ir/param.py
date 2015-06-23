from enum import Enum

class IRParameter:
    _IRParameterKind = Enum('IRParameterKind', ['OPT_ARG', 'ARG', 'ARG_NAT', 'MULT'])

    OPT_ARG = _IRParameterKind.OPT_ARG
    ARG = _IRParameterKind.ARG
    ARG_NAT = _IRParameterKind.ARG_NAT
    MULT = _IRParameterKind.MULT

    def __init__(self, kind, ir_ident, arg_type):
        self._kind = IRParameter._IRParameterKind(kind)
        self._ir_ident = ir_ident
        self._arg_type = arg_type

    @property
    def arg_type(self):
        return self._arg_type

    @property
    def ir_ident(self):
        return self._ir_ident

    def is_bare(self):
        return self._ir_ident.is_bare()

    def is_boxed(self):
        return self._ir_ident.is_boxed()

    @property
    def ident_full(self):
        return self._ir_ident.ident_full
    
    def __repr__(self):
        fmt='<IRParameter({}): kind={}, arg_type={}>'
        return fmt.format(self, self.kind, self.arg_type)

    def __str__(self):
        if self._kind == IRParameter.MULT:
            return '[ {} ]'.format(self.arg_type)
        return '{}:{}'.format(self.ident_full, self.arg_type)
