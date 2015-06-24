from .combinator import Python34Combinator
from .param import Python34Parameter
from .type import Python34Type
from .ident import Python34Identifier

from ..targets import Target
from collections import OrderedDict

con_num_struct='''
_pack_number_struct = Struct('<I')
pack_number = _pack_number_struct.pack
'''

int_c="""
class int_c:
    number = pack_number(0xa8509bda)

    _struct = Struct('<i')

    @staticmethod
    def deserialize(io_bytes):
        return int_c._struct.unpack(io_bytes.read(4))[0]
combinators[int_c.number] = int_c
"""

long_c="""
class long_c:
    number = pack_number(0x22076cba)

    _struct = Struct('<q')

    @staticmethod
    def deserialize(io_bytes):
        return long_c._struct.unpack(io_bytes.read(8))[0]     
combinators[long_c.number] = long_c
"""

double_c="""
class double_c:
    number = pack_number(0x2210c154)

    _struct = Struct('<d')

    @staticmethod
    def deserialize(io_bytes):
        return double_c._struct.unpack(io_bytes.read(8))[0]    
combinators[double_c.number] = double_c
"""

string_c="""
class string_c:
    number = pack_number(0xb5286e24)

    @staticmethod
    def deserialize(io_bytes):
        size = int.from_bytes(io_bytes.read(1), byteorder='little')
        pfx_bytes = 1
        if size == 254:
            size = int.from_bytes(io_bytes.read(3), byteorder='little')
            pfx_bytes = 4

        result = io_bytes.read(size)

        remainder = 4 - (pfx_bytes + size)%4
        io_bytes.read(remainder)

        return result.decode()
combinators[string_c.number] = string_c
"""

bytes_c="""
class bytes_c:
    number = pack_number(0xebefb69e)

    @staticmethod
    def deserialize(io_bytes):
        size = int.from_bytes(io_bytes.read(1), byteorder='little')
        pfx_bytes = 1
        if size == 254:
            size = int.from_bytes(io_bytes.read(3), byteorder='little')
            pfx_bytes = 4

        result = io_bytes.read(size)

        remainder = 4 - (pfx_bytes + size)%4
        io_bytes.read(remainder)

        return result
combinators[bytes_c.number] = bytes_c
"""

base_types=['int', 'Int', 'long', 'Long', 'double', 'Double', 'string', 'String', 'bytes', 'Bytes']
base_templates=[con_num_struct, int_c, long_c, double_c, string_c, bytes_c]

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
