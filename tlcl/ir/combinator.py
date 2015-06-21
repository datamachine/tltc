from enum import Enum

from .identifier import IRIdentifier
from .param import IRParameter
from .type import IRType

class IRCombinator:
    _IRCombinatorKind = Enum('IRCombinatorKind', ['CONSTRUCTOR', 'FUNCTION'])

    CONSTRUCTOR = _IRCombinatorKind.CONSTRUCTOR
    FUNCTION = _IRCombinatorKind.FUNCTION

    def __init__(self, kind, identifier, number=None, params=[], result_type=None):
        self._kind = IRCombinator._IRCombinatorKind(kind)
        self._identifier = identifier
        self._number = number
        self._params = params
        self._result_type = result_type

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
    
    def add_parameter(self, param):    
        self._params.append(param)
        
    def set_result_type(self, result_type):
        self._result_type = result_type
    

