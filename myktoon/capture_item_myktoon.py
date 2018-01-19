#!/usr/bin/env python3

import io
import os
import sys
import re
import getopt
import feedmakerutil


def main():
    numOfRecentFeeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    lineList = feedmakerutil.readStdinAsLineList()
    timesseq = ""
    title = ""
    resultList = []
    for line in lineList:
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
                resultList.append((link, title))
                timesseq = ""
                title = ""

    for (link, title) in resultList[:numOfRecentFeeds]:
        print("%s\t%s" % (link, title))

        
if __name__ == "__main__":
	main()

