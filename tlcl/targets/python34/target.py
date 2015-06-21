from .combinator import Python34Combinator
from .param import Python34Parameter
from .type import Python34Type
from ..targets import Target
from collections import OrderedDict

BUILTIN_COMBINATORS = ['vector', 'int', 'long', 'double', 'bool', 'string', 'bytes']

class Python34Target(Target):
    def __init__(self, schema):
        self.schema = schema
        self.combinators = OrderedDict()
        self.types = OrderedDict()
        self.preprocess()

    def preprocess(self):
        for name, t in self.schema.types.items():
            self.types[name] = Python34Type(self, t)

        for name, c in self.schema.combinators_by_identifier.items():
            if name in BUILTIN_COMBINATORS:
                print('Skipping built-in type "{}"'.format(name))
                continue
            combinator = Python34Combinator(self, c)
            self.combinators[c.identifier.full_ident] = combinator

        for name, c in self.combinators.items():
            print(c.definition())

        for n, t in self.types.items():
            print(t.constructors)

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
        pass
