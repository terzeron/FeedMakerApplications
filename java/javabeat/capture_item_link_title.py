#!/usr/bin/env python3


import io
import os
import sys
import re


def main():
    state = 0
    inputStream = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="ignore")
    for line in inputStream:
        m = re.search(r'a href="(?P<link>[^"]+)"[^>]*title="(?P<title>[^"]+)"', line)
        if m:
            link = m.group("link")
            title = m.group("title")
            print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    sys.exit(main())
