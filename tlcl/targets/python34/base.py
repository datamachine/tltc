
from abc import ABCMeta, abstractmethod
import numbers
from enum import Enum

import zlib

"""
Types used as base classes for TL combinators and types
"""
class TLType(metaclass=ABCMeta):
    _TLTypeKind = Enum('TLTypeKind', ['BARE', 'BOXED'])
    BARE = _TLTypeKind.BARE
    BOXED = _TLTypeKind.BOXED

    @abstractmethod
    def serialize(self):
        raise NotImplemented

    #@abstractmethod
    #def deserialize(self):
    #    raise NotImplemented

class Combinator(metaclass=ABCMeta):
    _combinators = {}

    @staticmethod
    def add_combinator(combinator_type):
        Combinator.combinators[combinator.number] = combinator_type

    @staticmethod
    @abstractmethod
    def serialize(obj):
        raise NotImplemented

    @staticmethod
    @abstractmethod
    def deserialize(self, bytes_io):
        raise NotImplemented

"""
_TLIntegralType utility base class used by Integral base type
"""
class _TLIntegralType(TLType, numbers.Integral):
    def __bytes__(self):
        return self.serialize()

    @property
    @abstractmethod
    def data(self):
        return self._data

    """
    Abstract methods from numbers.Integral
    """
    def __int__(self):
        return self.data.__int__()

    def __pow__(self, exponent, modulus=None):
        return self.data.__pow__(exponent, modulus)

    def __lshift__(self, other):
        return self.data.__lshift__(other)

    def __rlshift__(self, other):
        return self.data.__rlshift__(other)

    def __rshift__(self, other):
        return self.data.__rshift__(other)

    def __rrshift__(self, other):
        return self.data.__rrshift__(other)

    def __and__(self, other):
        return self.data.__and__(other)

    def __rand__(self, other):
        return self.data.__rand__(other)

    def __xor__(self, other):
        return self.data.__xor__(other)

    def __rxor__(self, other):
        return self.data.__rxor__(other)

    def __or__(self, other):
        return self.data.__or__(other)

    def __ror__(self, other):
        return self.data.__ror__(other)

    def __invert__(self):
        return self.data.__invert__(other)

    """
    Abstract methods from numbers.Real
    """        
    def __trunc__(self):
        return self.data.__trunc__(other)

    def __floor__(self):
        return self.data.__floor__(other)

    def __ceil__(self):
        return self.data.__ceil__(other)

    def __round__(self, ndigits=None):
        return self.data.__round__(ndigits)

    def __floordiv__(self, other):
        return self.data.__floordiv__(other)

    def __rfloordiv__(self, other):
        return self.data.__rfloordiv__(other)
        
    def __mod__(self, other):
        return self.data.__mod__(other)
        
    def __rmod__(self, other):
        return self.data.__rmod__(other)
        
    def __lt__(self, other):
        return self.data.__lt__(other)
        
    def __le__(self, other):
        return self.data.__le__(other)


    """
    Abstract methods from numbers.Complex
    """
    def __add__(self, other):
        return self.data.__add__(other)

    def __radd__(self, other):
        return self.data.__radd__(other)

    def __neg__(self):
        return self.data.__neg__()

    def __pos__(self):
        return self.data.__pos__()

    def __mul__(self, other):
        return self.data.__mul__(other)

    def __rmul__(self, other):
        return self.data.__rmul__(other)

    def __truediv__(self, other):
        return self.data.__truediv__(other)

    def __rtruediv__(self, other):
        return self.data.__rtruediv__(other)

    def __rpow__(self, base):
        return self.data.__rpow__(base)

    def __abs__(self):
        return self.data.__abs__()

    def __eq__(self, other):
        return self.data.__eq__(other)


"""
Int https://core.telegram.org/type/int
"""
class Int(_TLIntegralType):
    _cls = int

    def __init__(self, _int):
        self._int = Int._cls(_int)

    @property
    def data(self):
        return self._int

    def __repr__(self):
        return 'Int({:d})'.format(self._int)

    def serialize(self):
        return self._int.to_bytes(4, byteorder='little')

    def __format__(self, format_spec):
        if 'x' in format_spec or 'b' in format_spec:
            return format(int.from_bytes(self.serialize(), byteorder='big'), format_spec)
        return format(self._int, format_spec)
Int.register(Int._cls)

"""
Long https://core.telegram.org/type/long
"""
class Long(_TLIntegralType):
    _cls = int     

    def __init__(self, _long):
        self._long = Long._cls(_long)

    @property
    def data(self):
        return self._long

    def serialize(self):
        return self._long.to_bytes(8, byteorder='little')

    def __format__(self, format_spec):
        if 'x' in format_spec or 'b' in format_spec:
            return format(int.from_bytes(self.serialize()[0], byteorder='big'), format_spec)
        return format(self._long, format_spec)

"""
Bool https://core.telegram.org/type/bool
"""
class Bool(_TLIntegralType):
    _cls = bool

    _true = zlib.crc32('boolTrue = Bool'.encode())
    _false = zlib.crc32('boolFalse = Bool'.encode()) 

    def __init__(self, _bool):
        self._bool = Bool._cls(_bool)

    @property
    def data(self):
        return self._bool

    def serialize(self):
        if self._bool:
            return self._true.to_bytes(4, byteorder='little')
        else:
            return self._false.to_bytes(4, byteorder='little')

    def pseudo_serialize(self):
        return '{:#x}'.format(self._true if self._bool else self._false)
Bool.register(Bool._cls)

class Double(numbers.Real):
    def __init__(self, _double):
        super().__init__(_double)

    def serialize(self):
            return format(int.from_bytes(self.serialize()[0], byteorder='big'), format_spec)

Double.register(float)


"""
String https://core.telegram.org/type/string
"""
class String(TLType):
    def __init__(self, data):
        self._str = str(data)

    def __bytes__(self):
        return self._str.encode('utf-8')

    def serialize(self):
        result = bytearray()

        str_bytes = bytes(self)

        length = len(str_bytes)
        if length <= 253:
            result += length.to_bytes(1, byteorder='little')
        else:
            result += int(254).to_bytes(1, byteorder='little')
            result += length.to_bytes(3, byteorder='little')

        result += str_bytes
        
        result += bytes(4-len(result)%4)

        return bytes(result)

"""
String https://core.telegram.org/type/string
"""
class Bytes(TLType):
    def __init__(self, source, encoding=None, errors=None):
        if encoding is None and errors is None:
            self._bytes = bytes(source)
        elif encoding is None:
            self._bytes = bytes(source, errors=errors)
        elif errors is None:
            self._bytes = bytes(source, encoding=encoding)
        else:
            self._bytes = bytes(source, encoding=encoding, errors=errors)

    def __bytes__(self):
        return self._bytes

    def serialize(self):
        result = bytearray()

        length = len(self._bytes)
        if length <= 253:
            result += length.to_bytes(1, byteorder='little')
        else:
            result += int(254).to_bytes(1, byteorder='little')
            result += length.to_bytes(3, byteorder='little')
        
        result += self._bytes

        result += bytes(4-len(result)%4)

        return bytes(result)
