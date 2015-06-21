#!/usr/bin/env python3.4

from tlcl.targets.python34.base import *
from tlcl.targets.python34.builtin import *

if __name__ == '__main__':
    i = BaseInt(0x1020abcd)
    print('{:x}'.format(i))
    print(repr(i))

    s = BaseString('test')
    print(s.serialize())

    b = BaseBytes(255)
    print(b.serialize())