from .base import TLType

"""
https://core.telegram.org/type/vector_t
https://core.telegram.org/constructor/vector
"""
class Vector:
    def __init__(self, tl_type, data):
        self._tl_type = tl_type
        self._data = [tl_type(d) for d in data]

    def serialize(self):
        result = bytearray()
        for data in self._data:
            result += data.serialize()
        return bytes(result)

    def pseudo_serialize(self):
        result = []
        for data in self._data:
            result += [data.pseudo_serialize()]
        return ' '.join(result)
