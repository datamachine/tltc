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
    def identifier(self):
        return self._ir_ident.identifier

    def __repr__(self):
        fmt='<IRParameter({}): kind={}, arg_type={}>'
        return fmt.format(self, self.kind, self.arg_type)

    def __str__(self):
        return '{}:{}'.format(self.identifier, self.arg_type)
