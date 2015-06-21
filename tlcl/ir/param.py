from enum import Enum

class IRParameter:
    _IRParameterKind = Enum('IRParameterKind', ['OPT_ARG', 'ARG', 'ARG_NAT', 'MULT'])

    OPT_ARG = _IRParameterKind.OPT_ARG
    ARG = _IRParameterKind.ARG
    ARG_NAT = _IRParameterKind.ARG_NAT
    MULT = _IRParameterKind.MULT

    def __init__(self, kind, param_ident, arg_type):
        self.kind = IRParameter._IRParameterKind(kind)
        self.param_ident = param_ident
        self.arg_type = arg_type

    def __repr__(self):
        fmt='<IRParameter: kind={}, param_ident={}, arg_type={}>'
        return fmt.format(self.kind, self.param_ident.full_ident, self.arg_type.identifier.full_ident)
