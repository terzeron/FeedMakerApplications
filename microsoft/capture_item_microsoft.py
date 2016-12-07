#!/usr/bin/env python3


import io
import os
import sys
import re
import feedmakerutil


def main():
    link = ""
    title = ""

    lineList = feedmakerutil.readStdinAsLineList()
    for line in lineList:
        m = re.search(r'''
        <a
        \s*
        href="(?P<url>[^"]+)"
        \s*
        rel="bookmark"
        >
        (?P<title>[^<]+)
        </a>
        ''', line, re.VERBOSE)
        if m:
            link = m.group("url")
            title = m.group("title")
            link = re.sub(r'&amp;', '&', link)
            print("%s\t%s" % (link, title))


if __name__ == "__main__":
    main()
