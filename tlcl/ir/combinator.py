from enum import Enum

class IRCombinator:
	_IRCombinatorKind = Enum('IRCombinatorKind', ['CONSTRUCTOR', 'FUNCTION'])

	CONSTRUCTOR = _IRCombinatorKind.CONSTRUCTOR
	FUNCTION = _IRCombinatorKind.FUNCTION

	def __init__(self, kind, identifier=None, number=None, params=[], result_type=None):
		self._kind = _IRCombinatorKind(kind)
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
	
	

