from abc import ABCMeta, abstractmethod

class Target(metaclass=ABCMeta):
	@staticmethod
	@abstractmethod
	def name():
		raise NotImplemented

	@staticmethod
	@abstractmethod
	def description():
		raise NotImplemented

	@staticmethod
	@abstractmethod
	def combinator_cls():
		raise NotImplemented

	@staticmethod
	@abstractmethod
	def param_cls():
		raise NotImplemented

	@staticmethod
	@abstractmethod
	def type_cls():
		raise NotImplemented

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

	def init_target(self, target):
		if target not in self._targets:
			raise Exception("Target does not exists: '{}'".format(target))

Targets = _Targets()

