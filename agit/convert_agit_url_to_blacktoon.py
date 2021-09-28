#!/usr/bin/env python


import sys
import re
from feed_maker_util import IO


def main():
    for line in IO.read_stdin_as_line_list():
        line = re.sub(r'https://agit\d+.com/azi_toons/\d+/', 'https://img.blackmanaimg.com/', line)
        line = re.sub(r' ', '%20', line)
        print(line, end='')


if __name__ == "__main__":
    sys.exit(main())
