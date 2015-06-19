from .base import TLObject

"""
https://core.telegram.org/type/vector_t
https://core.telegram.org/constructor/vector
"""
class Vector(TLObject):
    def __init__(self, vector_type):
        if not isinstance(vector_type, type):
            raise TypeError('vector_type must be a type')
        self._type = vector_type
        self._data = []

    def serialize(self):
        result = b''
        for d in self._data:
            result += d.serialize()
        return result