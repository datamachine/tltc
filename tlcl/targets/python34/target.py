from .combinator import Python34Combinator
from .param import Python34Parameter
from .type import Python34Type
from .ident import Python34Identifier

from ..targets import Target
from collections import OrderedDict

class Python34Target(Target):
    def __init__(self, schema, types, combinators):
        self.schema = schema
        self.types = types
        self.combinators = combinators

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

    @staticmethod
    def ident_cls():
        return Python34Identifier

    def translate(self):
        print('from collections import namedtuple')
        try:
            for name, t in self.types.items():
                print(t.definition())
        except Exception as e:
            raise e

        for name, c in self.combinators.items():
            try:
                print(c.definition())
            except Exception as e:
                print(c)
                print(e)
                raise e

        for name, c in self.combinators.items():
            print('{}.deserialize(bytes(2000))'.format(c.py3ident))
