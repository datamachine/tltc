
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
_Integral utility base class used by Integral base type
"""
class _Integral(numbers.Integral, TLObject):
    def __init__(self, _data):
        self._data = type(self)._cls(_data)

    def serialize(self):
        return type(self)._cls._struct.pack(self._data)

    def __bytes__(self):
        return self.serialize()

    def __format__(self, format_spec):
        if 'x' in format_spec or 'b' in format_spec:
            return format(struct.unpack('<L', self.serialize())[0], format_spec)
        return format(self._data, format_spec)

    """
    Abstract methods from numbers.Integral
    """
    def __int__(self):
        return self._data.__int__()

    def __pow__(self, exponent, modulus=None):
        return self._data.__pow__(exponent, modulus)

    def __lshift__(self, other):
        return self._data.__lshift__(other)

    def __rlshift__(self, other):
        return self._data.__rlshift__(other)

    def __rshift__(self, other):
        return self._data.__rshift__(other)

    def __rrshift__(self, other):
        return self._data.__rrshift__(other)

    def __and__(self, other):
        return self._data.__and__(other)

    def __rand__(self, other):
        return self._data.__rand__(other)

    def __xor__(self, other):
        return self._data.__xor__(other)

    def __rxor__(self, other):
        return self._data.__rxor__(other)

    def __or__(self, other):
        return self._data.__or__(other)

    def __ror__(self, other):
        return self._data.__ror__(other)

    def __invert__(self):
        return self._data.__invert__(other)

    """
    Abstract methods from numbers.Real
    """        
    def __trunc__(self):
        return self._data.__trunc__(other)

    def __floor__(self):
        return self._data.__floor__(other)

    def __ceil__(self):
        return self._data.__ceil__(other)

    def __round__(self, ndigits=None):
        return self._data.__round__(ndigits)

    def __floordiv__(self, other):
        return self._data.__floordiv__(other)

    def __rfloordiv__(self, other):
        return self._data.__rfloordiv__(other)
        
    def __mod__(self, other):
        return self._data.__mod__(other)
        
    def __rmod__(self, other):
        return self._data.__rmod__(other)
        
    def __lt__(self, other):
        return self._data.__lt__(other)
        
    def __le__(self, other):
        return self._data.__le__(other)


    """
    Abstract methods from numbers.Complex
    """
    def __add__(self, other):
        return self._data.__add__(other)

    def __radd__(self, other):
        return self._data.__radd__(other)

    def __neg__(self):
        return self._data.__neg__()

    def __pos__(self):
        return self._data.__pos__()

    def __mul__(self, other):
        return self._data.__mul__(other)

    def __rmul__(self, other):
        return self._data.__rmul__(other)

    def __truediv__(self, other):
        return self._data.__truediv__(other)

    def __rtruediv__(self, other):
        return self._data.__rtruediv__(other)

    def __rpow__(self, base):
        return self._data.__rpow__(base)

    def __abs__(self):
        return self._data.__abs__()

    def __eq__(self, other):
        return self._data.__eq__(other)


"""
BaseInt https://core.telegram.org/type/int
"""
class BaseInt(_Integral):
    _cls = int
    _struct = struct.Struct('!l')

    def __init__(self, _int):
        super().__init__(_int)

    def serialize(self):
        return BaseInt._struct.pack(self._data)

    def __repr__(self):
        return 'BaseInt({:d})'.format(self._data)

    def __bytes__(self):
        return self.serialize()

    def __format__(self, format_spec):
        if 'x' in format_spec or 'b' in format_spec:
            return format(struct.unpack('<L', self.serialize())[0], format_spec)
        return format(self._data, format_spec)
BaseInt.register(BaseInt._cls)

"""
BaseLong https://core.telegram.org/type/long
"""
class BaseLong(_Integral):
    _cls = int     
    _struct = struct.Struct('!q')

    def __init__(self, _long):
        super().__init__(_long)

    def __init__(self, _long):
        self._data = int(_long)

    def serialize(obj):
        return BaseLong._struct.pack(self._data)
BaseLong.register(BaseLong._cls)

"""
BaseBool https://core.telegram.org/type/bool
"""
class BaseBool(_Integral):
    _cls = bool
    _struct = struct.Struct('!q')

    def __init__(self, _bool):
        super().__init__(_bool)

    def serialize(obj):
        return BaseBool._struct.pack(self._data)
BaseBool.register(BaseBool._cls)

class Double(numbers.Real, TLObject):
    _struct = struct.Struct('!d')

    def __init__(self, _double):
        super().__init__(_double)

    def serialize(self):
        return Double._struct.pack(self._data)
Double.register(float)
