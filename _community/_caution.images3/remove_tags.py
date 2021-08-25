#!/usr/bin/env python

import sys
import re


def main():
    for line in sys.stdin:
        if re.search(r'</?(article|html|head|body)>', line):
            line = re.sub(r'</?(article|html|head|body)>', '', line)
        print(line, end='')


if __name__ == "__main__":
    sys.exit(main())
