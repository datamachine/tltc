from enum import Enum

class IRParameter:
    _IRParameterKind = Enum('IRParameterKind', ['OPT_ARG', 'ARG'])

    OPT_ARG = _IRParameterKind.OPT_ARG
    ARG = _IRParameterKind.ARG

    def __init__(self, kind, param_ident, arg_type):
        self.kind = IRParameter._IRParameterKind(kind)
        self.param_ident = param_ident
        self.arg_type = arg_type
