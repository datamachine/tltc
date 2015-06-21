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
        for combinator in self.schema.combinators:
            print(combinator)
        types = {}
        for name, ir_type in self.schema.types.items():
            if name in ['Vector t', 'Bool', 'Null']:
                print('skipping built-in type: "{}"'.format(name))
                continue

            t = Python34Type(self, ir_type)
            types[ir_type.identifier.full_ident] = t

        for name, t in types.items():
            t.preprocess_member_inits(types)

        for name, t in types.items():
            print('{:type_definition}'.format(t))


        #for name, t in types.items():
        #    print(t.definition(validate=False))