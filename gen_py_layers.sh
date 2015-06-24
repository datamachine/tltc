#!/bin/bash

for layer in $(ls schemas/telegram/layer*)
do
    python3.4 -m tlcl.compile -t Python3.4 ${layer} > output/py34/tl/$(basename ${layer%.tl}.py)
done
