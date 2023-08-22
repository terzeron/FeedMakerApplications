#!/usr/bin/env python

import io
import os
import sys
import re
import getopt
from bin.feed_maker_util import IO


def main():
    num_of_recent_feeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    timesseq = ""
    title = ""
    result_list = []
    for line in line_list:
        matches = re.findall(r'"(\w+)"\s*:\s*"?([^"},]*)"?\s*', line)
        for match in matches:
            key = match[0]
            value = match[1]
            if key == "timesseq":
                timesseq = value
            elif key == "timestitle":
                title = value
            if timesseq != "" and title != "":
                link = "https://v2.myktoon.com/web/works/viewer.kt?timesseq=" + timesseq
                result_list.append((link, title))
                timesseq = ""
                title = ""

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

        
if __name__ == "__main__":
	sys.exit(main())

