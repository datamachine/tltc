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
		ident_cls = target_cls.ident_cls()

		types = OrderedDict()
		combinators = OrderedDict()

		def convert_type(ir_type):
			return type_cls(ident_cls(ir_type.ir_ident), ir_type)

		for name, ir_type in schema.types.items():
			tgt_type = convert_type(ir_type)
			types[ir_type.ident_full] = tgt_type

		for name, ir_combinator in schema.combinators.items():
			params = []
			for ir_param in ir_combinator.params:
				arg_type = types.get(ir_param.arg_type.ident_full)

				if arg_type is None:
					print('WARNING: {} in parameter "{}"; unkown arg type: {}'.format(ir_combinator, ir_param, ir_param.arg_type), file=stderr)
					continue
				param = param_cls(ident_cls(ir_param.ir_ident), arg_type, ir_param)
				params.append(param)

			result_type = types.get(ir_combinator.result_type.ident_full)
			if result_type is None:
				result_type = str(ir_combinator.result_type)
				print('WARNING: {} unkown combinator result type: {}'.format(ir_combinator, result_type), file=stderr)

			combinator = combinator_cls(
				ident=ident_cls(ir_combinator.ir_ident),
				params=params,
				result_type=result_type,
				ir_combinator=ir_combinator
				)

			combinators[str(ir_combinator)] = combinator

		target = target_cls(schema, types, combinators)

		return target

Targets = _Targets()

