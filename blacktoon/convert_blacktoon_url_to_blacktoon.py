#!/usr/bin/env python


import sys
import re
from feed_maker_util import IO


def main():
    for line in IO.read_stdin_as_line_list():
        line = re.sub(r'https://blacktoon\d+.com/webtoons/\d+/', 'https://image.blackmanaimg.com/', line)
        if re.search(r'<img src=', line):
            line = re.sub(r' ', '%20', line)
            line = re.sub(r'<img%20src', '<img src', line)
        line = re.sub(r'\[', '%5B', line)
        line = re.sub(r'\]', '%5D', line)
        print(line, end='')


if __name__ == "__main__":
    sys.exit(main())
