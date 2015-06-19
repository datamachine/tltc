class Target(dict):
	def __init__(self, name, description, combinator_cls, param_cls, type_cls):
		self.name = name
		self.description = description
		self.combinator_cls = combinator_cls
		self.param_cls = param_cls
		self.type_cls = type_cls

class _Targets:
	def __init__(self):
		self._targets = {}

	def add(self, target):
		self._targets[target.name] = target

	def add_new(self, name, description, combinator_cls, param_cls, type_cls):
		self.add(Target(name=name, description=description, combinator_cls=combinator_cls, param_cls=param_cls, type_cls=type_cls))

	def available(self):
		return [t for t in self._targets]

	def exists(self, name):
		return name in self._targets

	def get(self, name):
		return self._targets.get(name, None)

Targets = _Targets()

