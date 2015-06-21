from abc import ABCMeta, abstractmethod

class Target(metaclass=ABCMeta):
	@abstractmethod
	def translate(self):
		print('test')

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

	def get_target(self, target_name):
		if target_name not in self._targets:
			raise Exception("Target does not exists: '{}'".format(target_name))

		return self._targets[target_name]

	def init_target(self, target_name, schema):
		target_cls = self.get_target(target_name)
		return target_cls(schema)

Targets = _Targets()

