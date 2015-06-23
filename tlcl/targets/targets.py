from abc import ABCMeta, abstractmethod
from collections import OrderedDict

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

	@staticmethod
	@abstractmethod
	def ident_cls():
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
		from sys import stderr

		target_cls = self.get_target(target_name)
		type_cls = target_cls.type_cls()
		param_cls = target_cls.param_cls()
		combinator_cls = target_cls.combinator_cls()

		target = target_cls(schema)

		types = OrderedDict()
		combinators = OrderedDict()

		for name, ir_type in schema.types.items():
			tgt_type = type_cls(ir_type)
			types[str(ir_type)] = tgt_type

		for name, ir_combinator in schema.combinators.items():
			params = []
			for ir_param in ir_combinator.params:
				arg_type = types.get(str(ir_param.arg_type))
				if arg_type is None:
					arg_type = str(ir_param.arg_type)
					print('WARNING: {} in parameter "{}"; unkown arg type: {}'.format(ir_combinator, ir_param, ir_param.arg_type), file=stderr)
				param = param_cls(ir_param, arg_type)
				params.append(param)

			result_type = types.get(str(ir_combinator.result_type))
			if result_type is None:
				result_type = str(ir_combinator.result_type)
				print('WARNING: {} unkown combinator result type: {}'.format(ir_combinator, result_type), file=stderr)

			combinator = combinator_cls(
				ir_combinator=ir_combinator,
				params=params,
				result_type=result_type
				)

			combinators[str(ir_combinator)] = combinator

		return target

Targets = _Targets()

