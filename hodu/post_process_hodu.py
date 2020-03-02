#!/usr/bin/env python


import sys
import re
import json
from feed_maker_util import IO


def main():
    for line in IO.read_stdin_as_line_list():
        matches = re.findall(r'(<img[^>]*src=(?:["\'])[^\"\']+(?:["\'])[^>]*>)', line)
        for m in matches:
            print(m)


if __name__ == "__main__":
    sys.exit(main())
