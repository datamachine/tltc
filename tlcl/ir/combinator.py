from enum import Enum

class IRCombinator:
	_IRCombinatorKind = Enum('IRCombinatorKind', ['CONSTRUCTOR', 'FUNCTION'])

	CONSTRUCTOR = _IRCombinatorKind.CONSTRUCTOR
	FUNCTION = _IRCombinatorKind.FUNCTION

	def __init__(self, kind, identifer, number, params, result_type):
		self.kind = _IRCombinatorKind(kind)
		self.identifer = identifer
		self.number = number
		self.params = params
		self.result_type = result_type
