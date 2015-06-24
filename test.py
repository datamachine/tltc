#!/usr/bin/env python3.4

import io
import py34types as py3

def deserialize(io_bytes):
    constructor = io_bytes.read(4)
    cons = py3.combinators[constructor]
    return cons.deserialize(io_bytes)


def test_long():
    val = int(12345678)

    _bytes = bytearray(py3.long_c.number)
    _bytes += val.to_bytes(8, byteorder='little')

    io_bytes = io.BytesIO(_bytes)
    result = deserialize(io_bytes)

    assert len(io_bytes.read()) == 0, 'Failed to read all the data in test_long'
    assert val == result, 'Error deserializing int(%d)' %val

def test_int():
    val = int(1234)

    _bytes = bytearray(py3.int_c.number)
    _bytes += val.to_bytes(4, byteorder='little')

    io_bytes = io.BytesIO(_bytes)
    result = deserialize(io_bytes)

    assert len(io_bytes.read()) == 0, 'Failed to read all the data in test_long'
    assert val == result, 'Error deserializing int(%d)' %val



if __name__ == '__main__':
    test_int()
    test_long()