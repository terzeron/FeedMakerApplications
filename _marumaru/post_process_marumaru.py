#!/usr/bin/env python


import re
import sys


def main() -> int:
    for line in sys.stdin:
        if re.search(r'<meta|style', line):
            print(line, end='')
        match = re.search(r'<img src=[\'"]?(?P<img_url>https?://[^\'"]+)[\'"]?[^>]*>', line)
        if match:
            img_url = match.group('img_url')
            img_url = re.sub(r' ', '%20', img_url)
            print("<img src='%s'>" % img_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
