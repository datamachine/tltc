#!/usr/bin/env python3.4

import io
import py34types as p3

def deserialize(io_bytes):
    constructor = io_bytes.read(4)
    cons = p3.combinators[constructor]
    return cons.deserialize(io_bytes)


def test_long():
    _bytes = bytearray()
    _bytes += int(0xa8509bda).to_bytes(4, byteorder='little')
    _bytes += int(1234).to_bytes(4, byteorder='little')

    io_bytes = io.BytesIO(_bytes)
    result = deserialize(io_bytes)

    print(io_bytes.read())
    print(result)

def test_int():
    _bytes = bytearray()
    _bytes += int(0xa8509bda).to_bytes(4, byteorder='little')
    _bytes += int(1234).to_bytes(4, byteorder='little')

    io_bytes = io.BytesIO(_bytes)
    result = deserialize(io_bytes)

    print(io_bytes.read())
    print(result)



if __name__ == '__main__':
    test_int()