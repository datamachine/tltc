from enum import Enum
from collections import OrderedDict

from .identifier import IRIdentifier
from .param import IRParameter
from .type import IRType

class IRCombinator:
    _IRCombinatorKind = Enum('IRCombinatorKind', ['CONSTRUCTOR', 'FUNCTION'])

    CONSTRUCTOR = _IRCombinatorKind.CONSTRUCTOR
    FUNCTION = _IRCombinatorKind.FUNCTION

    def __init__(self, kind, identifier, number):
        self._kind = IRCombinator._IRCombinatorKind(kind)
        self._identifier = identifier
        self._number = number
        self._params = []
        self._result_type = None

    @property
    def kind(self):
        return self._kind

    @property
    def identifier(self):
        return self._identifier
    
    @property
    def number(self):
        return self._number
    
    @property
    def params(self):
        return self._params
    
    @property
    def result_type(self):
        return self._result_type

    @property
    def lc_ident_full(self):
        return '{}#{:x}'.format(str(self.identifier), self.number)
    
    
    def add_parameter(self, param):    
        self._params.append(param)
        
    def set_result_type(self, result_type):
        result_type.constructors.append(self)
        self._result_type = result_type

    def __repr__(self):
        fmt='<IRCombinator: kind={}, identifier={}, number={:x}, params={}, result_type={}>'
        ps = ['{}:{}'.format(str(p.param_ident), str(p.arg_type.identifier)) for p in self.params]
        ps = '[' + ', '.join(ps) + ']'
        return fmt.format(self.kind, str(self.identifier), self.number, ps, self.result_type)

    def __str__(self):
        return self.lc_ident_full

