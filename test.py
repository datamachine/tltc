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

if __name__ == '__main__':
    test_int()
    test_long()
    test_double()
    test_string()
    test_bytes()