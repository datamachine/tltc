from .combinator import Python34Combinator
from .param import Python34Parameter
from .type import Python34Type
from .ident import Python34Identifier

from ..targets import Target
from collections import OrderedDict

con_num_struct='''
def pack_number(num):
    return int(num).to_bytes(4, byteorder='little')
'''

int_c="""
class int_c:
    number = pack_number(0xa8509bda)

    @staticmethod
    def deserialize(io_bytes):
        return int.from_bytes(io_bytes.read(4), byteorder='little')      
combinators[int_c.number] = int_c
"""

long_c="""
class long_c:
    number = pack_number(0x22076cba)

    @staticmethod
    def deserialize(io_bytes):
        return int.from_bytes(io_bytes.read(8), byteorder='little')      
combinators[long_c.number] = long_c
"""

base_types=['int', 'Int', 'long', 'Long']
base_templates=[con_num_struct, int_c, long_c]

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
        print('from struct import Struct')
        print('import io')
        print('')
        print('combinators = {}')
        #try:
        #    for name, t in self.types.items():
        #        print(t.definition())
        #except Exception as e:
        #    raise e

        for t in base_templates:
            print(t)

        for name, c in self.combinators.items():
            try:
                if c.ident.ir_ident.ident_full not in base_types:
                    print(c.definition())
            except Exception as e:
                print(c, file=sys.stderr)
                print(e, file=sys.stderr)

        #for name, c in self.combinators.items():
        #    print('{}.deserialize(bytes(2000))'.format(c.py3ident))
