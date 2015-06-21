from abc import ABCMeta, abstractmethod

class Target(metaclass=ABCMeta):
	@staticmethod
	@abstractmethod
	def name():
		raise NotImplements

	@staticmethod
	@abstractmethod
	def description():
		raise NotImplements

	@staticmethod
	@abstractmethod
	def combinator_cls():
		raise NotImplements

	@staticmethod
	@abstractmethod
	def param_cls():
		raise NotImplements

	@staticmethod
	@abstractmethod
	def type_cls():
		raise NotImplements

	@staticmethod
	@abstractmethod
	def translator_cls():
		raise NotImplements

class _Targets:
	def __init__(self):
		self._targets = {}

	def add_target(self, target):
		self._targets[target.name()] = target

	def available(self):
		return self._targets.keys()

	def exists(self, name):
		return name in self._targets

	def get(self, name):
		return self._targets.get(name, None)

Targets = _Targets()

