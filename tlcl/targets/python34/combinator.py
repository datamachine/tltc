from collections import OrderedDict
from inspect import Signature, Parameter
from .param import Python34Parameter
from .ident import Python34Identifier

template="""
class {identifier}:
    number = pack_number({number:#x})
    is_base = False
    _result = namedtuple('{result_type}', [{result_type_params}])

    @staticmethod
    def deserialize(io_bytes):
        {deserialize}
combinators[{identifier}.number] = {identifier}
"""


class Python34Combinator:
    def __init__(self, ident, params, result_type, ir_combinator):
        self._ident = ident
        self._params = params
        self._result_type = result_type
        self._ir_combinator = ir_combinator

        result_type.add_constructor(self)


    def _set_result_type(self):
        result = self._ir_combinator.result_type
        result_type = self.target.types[result.identifier.full_ident]
        result_type.constructors[self._ir_combinator.identifier.full_ident] = self
        self._result_type = result_type

    @property
    def identifier(self):
        return self._ident.py3ident

    @property
    def ident(self):
        return self._ident

    @property
    def number(self):
        return self._ir_combinator.number

    @property
    def params(self):
        return self._params

    @property
    def py3ident(self):
        ident = '{}_c'.format(self._ident.py3ident)

        Python34Identifier.validate(ident)

        return ident
    
    def _template_identifier(self):
        return self.py3ident

    def _template_get_params(self):
        get_params = ['{} = {}.deserialize(io_bytes)'.format(p.py3ident, p.arg_type.py3ident) for p in self.params]
        return '\n        '.join(get_params)

    def _template_set_params(self):
        set_params = ['''setattr(result, '{0}', {0})'''.format(p.py3ident) for p in self.params]
        return '\n        '.join(set_params)

    def _template_result_type_params(self):
        get_params = ["'{}'".format(p.py3ident) for p in self.params]
        if not get_params:
            get_params = ["'tag'", "'number'"]
        return ', '.join(get_params)

    #def _template_result_type_params(self):
    #    get_params = ["_{0} = combinators[{number:#x}]".format(p.py3ident) for p in self.params]
    #    return ', '.join(get_params)

    def _template_result_type(self):
        return self.result_type.py3ident

    def _template_deserialize(self):
        if not self.params:
            return "return {0}._result(tag='{1}', number={0}.number)".format(self._template_identifier(),
                                                                      self.ident.ir_ident.ident_full)
        else:
            return 'pass'

    @property
    def result_type(self):
        return self._result_type

    def definition(self):
        return template.format(
            identifier=self._template_identifier(), 
            number=self.number, 
            result_type_params=self._template_result_type_params(),
            result_type=self._template_result_type(),
            deserialize=self._template_deserialize()
            )

    def __str__(self):
        return '{}#{:x}'.format(self.identifier, self.number)
