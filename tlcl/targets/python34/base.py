
from abc import ABCMeta, abstractmethod
import numbers
import struct

from functools import partial

"""
Types used as base classes for TL combinators and types
"""
class TLObject(metaclass=ABCMeta):
    @abstractmethod
    def serialize(self):
        raise NotImplemented

class TLType(metaclass=ABCMeta):
    def __init__(self):
        self._combinators = {}



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
Int https://core.telegram.org/type/int
"""
class Int(numbers.Integral, TLObject):
    _struct = struct.Struct('!L')

    def __init__(self, _int):
        self._int = int(_int)

    @property
    def _tl_type_class(self):
        return type(self)

    def serialize(self):
        return Int._struct.pack(self._int)

    def __repr__(self):
        return 'Int({})'.format(self._int)

    def __bytes__(self):
        return Int._struct.pack(self._int)

    def __format__(self, format_spec):
        if 'x' in format_spec or 'b' in format_spec:
            return format(struct.unpack('<L', self.serialize())[0], format_spec)
        return format(self._int, format_spec)

    """
    Abstract methods from numbers.Integral
    """
    def __int__(self):
        return self._int

    def __pow__(self, exponent, modulus=None):
        if modulus:
            return self._tl_type_class(self._int.__pow__(exponent, modulus=modulus))
        else:
            return self._tl_type_class(self._int.__pow__(exponent))

    def __lshift__(self, other):
        return self._tl_type_class(self._int.__lshift__(other))

    def __rlshift__(self, other):
        return self._tl_type_class(self._int.__rlshift__(other))

    def __rshift__(self, other):
        return self._tl_type_class(self._int.__rshift__(other))

    def __rrshift__(self, other):
        return self._tl_type_class(self._int.__rrshift__(other))

    def __and__(self, other):
        return self._tl_type_class(self._int.__and__(other))

    def __rand__(self, other):
        return self._tl_type_class(self._int.__rand__(other))

    def __xor__(self, other):
        return self._tl_type_class(self._int.__xor__(other))

    def __rxor__(self, other):
        return self._tl_type_class(self._int.__rxor__(other))

    def __or__(self, other):
        return self._tl_type_class(self._int.__or__(other))

    def __ror__(self, other):
        return self._tl_type_class(self._int.__ror__(other))

    def __invert__(self):
        return self._tl_type_class(self._int.__invert__())

    """
    Abstract methods from numbers.Real
    """        
    def __trunc__(self):
        return self._tl_type_class(self._int.__trunc__())

    def __floor__(self):
        return self._tl_type_class(self._int.__floor__())

    def __ceil__(self):
        return self._tl_type_class(self._int.__ceil__())

    def __round__(self, ndigits=None):
        return self._tl_type_class(self._int.__round__(ndigits=ndigits))

    def __floordiv__(self, other):
        return self._tl_type_class(self._int.__floordiv__(other))

    def __rfloordiv__(self, other):
        return self._tl_type_class(self._int.__rfloordiv__(other))
        
    def __mod__(self, other):
        return self._tl_type_class(self._int.__mod__(other))
        
    def __rmod__(self, other):
        return self._tl_type_class(self._int.__rmod__(other))
        
    def __lt__(self, other):
        return self._int.__lt__(other)
        
    def __le__(self, other):
        return self._int.__le__(other)


    """
    Abstract methods from numbers.Complex
    """
    def __add__(self, other):
        return self._tl_type_class(self._int.__add__(other))

    def __radd__(self, other):
        return self.classtype(self._int.__radd__(other))

    def __neg__(self):
        return self._tl_type_class(self._int.__neg__())

    def __pos__(self):
        return self._tl_type_class(self._int.__pos__())

    def __mul__(self, other):
        return self._tl_type_class(self._int.__mul__(other))

    def __rmul__(self, other):
        return self._tl_type_class(self._int.__rmul__(other))

    def __truediv__(self, other):
        return self._tl_type_class(self._int.__truediv__(other))

    def __rtruediv__(self, other):
        return self._tl_type_class(self._int.__rtruediv__(other))

    def __rpow__(self, base):
        return self._tl_type_class(self._int.__rpow__(exponent))

    def __abs__(self):
        return self._tl_type_class(self._int.__abs__())

    def __eq__(self, other):
        return self._int.__eq__(other)
Int.register(int)

"""
Long https://core.telegram.org/type/long
"""
class Long(Int, TLObject):        
    _struct = struct.Struct('!q')

    def __init__(self, _long):
        self._int = int(_long)

    @property
    def _internal_data_type(self):
        return int

    @property
    def _tl_type_class(self):
        return type(self)

    def serialize(obj):
        return Long._struct.pack(self._int)
Long.register(int)

"""
Bool https://core.telegram.org/type/bool
"""
class Bool(Int, TLObject):
    _struct = struct.Struct('!q')

    def __init__(self, _bool):
        self._int = bool(_bool)

    @property
    def internal_data_type(self):
        return bool

    @property
    def _tl_type_class(self):
        return type(self)

    def serialize(obj):
        return Bool._struct.pack(self._int)

Bool.register(bool)

class Double(numbers.Real, TLObject):
    _struct = struct.Struct('!d')

    def __init__(self, _double):
        self._int = float(_double)

    @property
    def _internal_data_type(self):
        return float 

    @property
    def _tl_type_class(self):
        return type(self) 

    def serialize(self):
        return Double._struct.pack(self._int)
Double.register(float)
