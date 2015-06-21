from enum import Enum

class IRParameter:
    _IRParameterKind = Enum('IRParameterKind', ['OPT_ARG', 'ARG', 'ARG_NAT'])

    OPT_ARG = _IRParameterKind.OPT_ARG
    ARG = _IRParameterKind.ARG
    ARG_NAT = _IRParameterKind.ARG_NAT

    def __init__(self, kind, param_ident, arg_type):
        self.kind = IRParameter._IRParameterKind(kind)
        self.param_ident = param_ident
        self.arg_type = arg_type
