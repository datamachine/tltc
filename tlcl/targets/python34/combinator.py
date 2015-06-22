from collections import OrderedDict
from inspect import Signature, Parameter
from .param import Python34Parameter

template="""
class {{identifier}}(TLCombinator):
    _number = {number:#x}

    @staticmethod
    def deserialize(io_bytes):
        return {{identifier}}.new(...)
"""

class Python34Combinator:
    def __init__(self, ir_combinator, params, result_type):
        self._ir_combinator = ir_combinator
        self._params = params
        self._result_type = result_type
        #self.target = target
        #self._ir_combinator = ir_combinator
        #self._params = None
        #self._number = ir_combinator.number
        #self._set_result_type()


    def _set_result_type(self):
        result = self._ir_combinator.result_type
        result_type = self.target.types[result.identifier.full_ident]
        result_type.constructors[self._ir_combinator.identifier.full_ident] = self
        self._result_type = result_type

    @property
    def identifier(self):
        return self._number

    @property
    def number(self):
        return self._ir_combinator.number

    @property
    def params(self):
        if self._params is not None:
            return self._params

        self._params = OrderedDict()
        for ir_param in self._ir_combinator.params:
            param = Python34Parameter(self.target, ir_param)
            self._params[ir_param.param_ident.full_ident] = param

        return self._params

    @property
    def result_type(self):
        return self._result_type

    def definition(self):
        return template.format(number=self.number)

    def __str__(self):
        return '{}#{:x}'.format(self.identifier, self.number)
