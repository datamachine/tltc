from inspect import Parameter

class Python34Parameter:
    def __init__(self, ir_param, arg_type):
        self._ir_param = ir_param
        self._arg_type = arg_type

    @property
    def identifier(self):
        return self._ir_param.param_ident.full_ident

    def declaration(self):
        return self._identifier

    def definition(self):
        return self._identifier

    @property
    def parameter(self):
        return Parameter(self.identifier, Parameter.POSITIONAL_OR_KEYWORD)
