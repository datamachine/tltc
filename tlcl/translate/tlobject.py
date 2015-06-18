from abc import ABCMeta, abstractmethod

class TLObject(metaclass=ABCMeta):
	@abstractmethod
	def __str__(self):
		raise NotImplemented()