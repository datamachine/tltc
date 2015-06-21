from .base import TLType

"""
https://core.telegram.org/type/vector_t
https://core.telegram.org/constructor/vector
"""
class Vector:
    def __init__(self, cls):
        if not isinstance(cls, type):
            raise TypeError('cls must be a type')
        self._cls = cls
        self._data = []

    def serialize(self):
        result = bytearray()
        for data in self._data:
            result += d.serialize()
        return result