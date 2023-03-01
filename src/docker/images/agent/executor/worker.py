#!/usr/bin/env -S python3 -u

import sys

print("Received message:")
for line in sys.stdin.readlines():
    print(line)

print("Done")
