#!/usr/bin/env python3.4

from python3builtins import *

import struct

if __name__ == '__main__':
    i = Int(1)
    print(type(i))
    print(bool(i))
    i = i + 4
    print(type(i))
    print(issubclass(int, Int))

    print(int(i))

    s1 = i.serialize()
    i = i + 1
    s2 = i.serialize()
    s3 = s1 + s2
    print(s3)

    v = Vector(Int)

    v._data += [Int(1), Int(4), Int(6)]
    print(v.serialize())