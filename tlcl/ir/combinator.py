from enum import Enum
from collections import OrderedDict

from .identifier import IRIdentifier
from .param import IRParameter
from .type import IRType

class IRCombinator:
    _combinators_by_identifier = OrderedDict()
    _combinators_by_number = OrderedDict()

    _IRCombinatorKind = Enum('IRCombinatorKind', ['CONSTRUCTOR', 'FUNCTION'])

    CONSTRUCTOR = _IRCombinatorKind.CONSTRUCTOR
    FUNCTION = _IRCombinatorKind.FUNCTION

    def __init__(self, kind, identifier, number, params=[], result_type=None):
        self._kind = IRCombinator._IRCombinatorKind(kind)
        self._identifier = identifier
        self._number = number
        self._params = params
        self._result_type = result_type

    @staticmethod
    def create_new(kind, identifier, number):
        if identifier.full_ident in IRCombinator._combinators_by_identifier:
            raise Exception('Combinator with identifier already exists: \'{:x}\''.format(identifier.full_ident))

        if number in IRCombinator._combinators_by_number:
            raise Exception('Combinator with number already exists: \'{:x}\''.format(number))

        combinator = IRCombinator(kind, identifier, number)

        IRCombinator._combinators_by_number[number] = combinator
        IRCombinator._combinators_by_identifier[identifier.full_ident] = combinator
        return combinator

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

    def __repr__(self):
        fmt='<IRCombinator: kind={}, identifier={}, number={:x}, params={}, result_type={}>'
        ps = ['{}:{}'.format(p.param_ident.full_ident, p.arg_type.identifier.full_ident) for p in self.params]
        ps = '[' + ', '.join(ps) + ']'
        return fmt.format(self.kind, self.identifier.full_ident, self.number, ps, self.result_type)

