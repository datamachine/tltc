from .combinator import Python34Combinator
from .param import Python34Parameter
from .type import Python34Type
from ..targets import Target

class Python34Target(Target):
    @staticmethod
    def name():
        return 'Python3.4'

    @staticmethod
    def description():
        return 'Only tested on Python 3.4'

    @staticmethod
    def combinator_cls():
        return Python34Combinator

    @staticmethod
    def param_cls():
        return Python34Parameter

    @staticmethod
    def type_cls():
        return Python34Type

    def translate(self):
        for name, ir_type in self.schema.types.items():
            t = Python34Type(self.schema, ir_type)
            t.preprocess()
            print(t.definition())
