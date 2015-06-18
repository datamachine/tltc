from .tlobject import TLObject

class Identifer(TLObject):
	def __new__(cls, identifier):
		

	def __str__(self):
		return self.identifier

class NamespaceIdentifier(Identifer):
	pass

class CombinatorIdentifer(TLObject):
	_combinators = []

	__slots__ = ('namespace', 'identifier')

	def __new__(cls, namespace, identifier):
		result = super(CombinatorIdentifer, cls).__new__(cls)
		result.namespace = NamespaceIdentifier(namespace)
		result.identifier = Identifer(identifier)
		# Combinator identifiers must be unique
		if result in CombinatorIdentifer._combinators:
			raise SyntaxError('Combinator already defined: {}'.format(CombinatorIdentifer._combinators))

		return result

	def __init__(self, namespace, identifier):
		pass

	def __str__(self):
		return '{}.{}'.format(self.namespace, self.identifier)

if __name__ == '__main__':
	ident = Identifer('myIdent')
	ns = NamespaceIdentifier('myNamespace')
	comb1 = CombinatorIdentifer('myNamespace', 'myIdent')
	comb2 = CombinatorIdentifer(ns, ident)

	print(ident)
	print(ns)
	print(comb1)
	print(comb2)