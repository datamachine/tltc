#!/usr/bin/env python3.4

import io
import tl

def test_int():
    val = int(1234)

    _bytes = bytearray(tl.int_c.number)
    _bytes += val.to_bytes(4, byteorder='little')

    io_bytes = io.BytesIO(_bytes)
    result = tl.deserialize(io_bytes)

    assert len(io_bytes.read()) == 0, 'Failed to read all the data'
    assert val == result, 'Error deserializing int(%d)' %val


def test_long():
    val = int(12345678)

    _bytes = bytearray(tl.long_c.number)
    _bytes += val.to_bytes(8, byteorder='little')

    io_bytes = io.BytesIO(_bytes)
    result = tl.deserialize(io_bytes)

    assert len(io_bytes.read()) == 0, 'Failed to read all the data'
    assert val == result, 'Error deserializing int(%d)' %val

def test_double():
    val = float(94.9)

    _bytes = bytearray(tl.double_c.number)
    _bytes += tl.double_c._struct.pack(val)

    io_bytes = io.BytesIO(_bytes)
    result = tl.deserialize(io_bytes)

    assert len(io_bytes.read()) == 0, 'Failed to read all the data'
    assert val == result, 'Error deserializing float(%f)' %val

def test_string():
    val = 'Peter'

    _bytes = bytearray(tl.string_c.number)
    _bytes += b'\x05' + val.encode() + b'\x00\x00'

    io_bytes = io.BytesIO(_bytes)
    result = tl.deserialize(io_bytes)

    assert len(io_bytes.read()) == 0, 'Failed to read all the data'
    assert result == 'Peter', 'Error reading %s' %_bytes

    val = 'Michael'
    result = tl.serialize(tl.string_c, val)

    assert result == b'\x07Michael', 'failed to serialize string'
    assert len(result)%4 == 0, 'string is not properly aligned'

def test_bytes():
    val = b'Parker'

    _bytes = bytearray(tl.bytes_c.number)
    _bytes += b'\x06' + val + b'\x00'

    io_bytes = io.BytesIO(_bytes)
    result = tl.deserialize(io_bytes)

    assert len(io_bytes.read()) == 0, 'Failed to read all the data'
    assert result == val, 'Error reading %s' %_bytes

    val = b'Jordan-Martinez'
    result = tl.serialize(tl.bytes_c, val)

    assert result == b'\x0FJordan-Martinez', 'failed to serialize bytes %s' %result
    assert len(result)%4 == 0, 'bytes are not properly aligned'

def test_vector():
    _bytes = bytearray(tl.vector_c.number)
    _bytes += int(5).to_bytes(4, byteorder='little')
    _bytes += int(10).to_bytes(4, byteorder='little')
    _bytes += int(20).to_bytes(4, byteorder='little')
    _bytes += int(30).to_bytes(4, byteorder='little')
    _bytes += int(40).to_bytes(4, byteorder='little')
    _bytes += int(50).to_bytes(4, byteorder='little')

    io_bytes = io.BytesIO(_bytes)
    result = tl.deserialize(io_bytes, tl.int_c)

    assert result == [10, 20, 30, 40, 50]

    val = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    result = tl.serialize(tl.vector_c, val, tl.int_c)

    ref = b'\x15\xC4\xB5\x1C\x0A\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00\x06\x00\x00\x00\x07\x00\x00\x00\x08\x00\x00\x00\x09\x00\x00\x00\x0A\x00\x00\x00'

    assert result == ref, 'incorrect serialization'

    io_bytes = io.BytesIO(result)
    result = tl.deserialize(io_bytes, tl.int_c)

    assert result == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

def test_bool():
    io_bytes = io.BytesIO(tl.boolTrue_c.number)
    result = tl.deserialize(io_bytes)
    assert result.tag == 'boolTrue', '"{} == {}"'.format(result.tag, 'boolTrue')
    assert result.number == tl.boolTrue_c.number, '"{} == {}"'.format(result.number, tl.boolTrue_c.number)

    io_bytes = io.BytesIO(tl.boolFalse_c.number)
    result = tl.deserialize(io_bytes)
    assert result.tag == 'boolFalse', '"{} == {}"'.format(result.tag, 'boolFalse')
    assert result.number == tl.boolFalse_c.number, '"{} == {}"'.format(result.number, tl.boolFalse_c.number)

if __name__ == '__main__':
    test_int()
    test_long()
    test_double()
    test_string()
    test_bytes()
    test_vector()
    test_bool()