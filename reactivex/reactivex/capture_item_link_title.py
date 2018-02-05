#!/usr/bin/env python

import sys
import re
import feedmakerutil


def main():
    link = ""
    title = ""

    line_list = feedmakerutil.read_stdin_as_line_list()
    for line in line_list:
        matches = re.findall(r'(?P<link>\S+)\t(?P<title>.+)', line)
        for match in matches:
            link = match[0]
            title = match[1]
            print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    sys.exit(main())
