from .combinator import Python34Combinator
from .param import Python34Parameter
from .type import Python34Type
from .ident import Python34Identifier

from ..targets import Target
from collections import OrderedDict

import sys

def_serialize='''
def serialize(combinator, *args, **kwargs):
    c = None
    if type(combinator) is int:
        c = combinators.get(combinator)
    else:
        c = combinators.get(combinator.number)
    if c is None:
        print('combinator "{}" does not exist'.format(combinator), file=sys.stderr)
        return None
    return c.serialize(*args, **kwargs)
'''

def_deserialize='''
def deserialize(io_bytes, *args, **kwargs):
    cons = combinators.get(io_bytes.read(4))
    if cons is None:
        print('combinator "{}" does not exist'.format(combinator), file=sys.stderr)
        return None

    if not cons.is_base:
        io_bytes.seek(-4, 1)
    
    return cons.deserialize(io_bytes, *args, **kwargs)
'''

con_num_struct='''
_pack_number_struct = Struct('<I')
pack_number = _pack_number_struct.pack
'''

int_c="""
class int_c:
    number = pack_number(0xa8509bda)
    is_base = True

    _struct = Struct('<i')

    @staticmethod
    def serialize(_int):
        return int_c._struct.pack(_int)

    @staticmethod
    def deserialize(io_bytes):
        return int_c._struct.unpack(io_bytes.read(4))[0]
combinators[int_c.number] = int_c
"""

long_c="""
class long_c:
    number = pack_number(0x22076cba)
    is_base = True

    _struct = Struct('<q')

    @staticmethod
    def serialize(_long):
        return long_c._struct.pack(_long)

    @staticmethod
    def deserialize(io_bytes):
        return long_c._struct.unpack(io_bytes.read(8))[0]     
combinators[long_c.number] = long_c
"""

double_c="""
class double_c:
    number = pack_number(0x2210c154)
    is_base = True

    _struct = Struct('<d')

    @staticmethod
    def serialize(_double):
        return double_c._struct.pack(_double)

    @staticmethod
    def deserialize(io_bytes):
        return double_c._struct.unpack(io_bytes.read(8))[0]    
combinators[double_c.number] = double_c
"""

string_c="""
class string_c:
    number = pack_number(0xb5286e24)
    is_base = True

    @staticmethod
    def serialize(string):
        result = bytearray()

        str_bytes = string.encode()

        size_pfx = len(str_bytes)
        if size_pfx < 254:
            result += size_pfx.to_bytes(1, byteorder='little')
        else:
            result += b'\\xfe'
            result += size_pfx.to_bytes(3, byteorder='little')

        result += str_bytes

        padding = len(result)%4
        result += bytes(padding)

        return bytes(result)


    @staticmethod
    def deserialize(io_bytes):
        size = int.from_bytes(io_bytes.read(1), byteorder='little')
        pfx_bytes = 1
        if size == 254:
            size = b'\\xfe'
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
    is_base = True

    @staticmethod
    def serialize(_bytes):
        result = bytearray()

        size_pfx = len(_bytes)
        if size_pfx < 254:
            result += size_pfx.to_bytes(1, byteorder='little')
        else:
            result += int(254).to_bytes(1, byteorder='little')
            result += size_pfx.to_bytes(3, byteorder='little')

        result += _bytes

        padding = len(result)%4
        result += bytes(padding)

        return bytes(result)

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

vector_c="""
class vector_c:
    number = pack_number(0x1cb5c415)
    is_base = True

    @staticmethod
    def serialize(iterable, vector_type):
        result = bytearray(vector_c.number)
        result += len(iterable).to_bytes(4, byteorder='little')
        for i in iterable:
            if not vector_type.is_base:
                result += vector_type.number
            result += vector_type.serialize(i)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes, vector_type=None):
        count = int.from_bytes(io_bytes.read(4), byteorder='little')
        items = []
        cons = None
        if vector_type is not None:
            cons = vector_type
        for i in range(count):
            if vector_type is None:
                cnum = int.from_bytes(io_bytes.read(4), byteorder='little')
                cons = combinators.get(cnum) 
            items.append(cons.deserialize(io_bytes))
        return items
combinators[vector_c.number] = vector_c
"""

base_types=['int', 'Int', 'long', 'Long', 'double', 'Double', 'string', 'String', 'bytes', 'Bytes', 'vector']
base_templates=[def_serialize, def_deserialize, con_num_struct, int_c, long_c, double_c, string_c, bytes_c, vector_c]

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
