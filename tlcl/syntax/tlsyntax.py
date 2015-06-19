from collections import OrderedDict
from .tokens import _CHARACTER_CLASSES, _SIMPLE_IDENTS_AND_KEYWORDS, _TOKENS

class TLSyntax:
	_definitions = OrderedDict()
	
	TL = OrderedDict()

	@staticmethod
	def add_definition(name, category_items):
		category_dict = OrderedDict()

		for key, val in category_items:
			val = val.format(**TLSyntax.TL)
			TLSyntax.TL[key] = val
			category_dict[key] = val

		TLSyntax._definitions[name] = category_dict
		setattr(TLSyntax, name, category_dict)

TLSyntax.add_definition('CHARACTER_CLASSES', _CHARACTER_CLASSES.items())
TLSyntax.add_definition('SIMPLE_IDENTS_AND_KEYWORDS', _SIMPLE_IDENTS_AND_KEYWORDS.items())
TLSyntax.add_definition('TOKENS', _TOKENS.items())
