#!/usr/bin/env python3.4

from tlcl.targets.python34.base import *
from tlcl.targets.python34.builtin import *

if __name__ == '__main__':
    i = Int(0x1020abcd)
    print('{:x}'.format(i))
    print(repr(i))

    s = String('test')
    print(s.serialize())

    _bool = Bool(True)
    print('boolTrue:', _bool.serialize())