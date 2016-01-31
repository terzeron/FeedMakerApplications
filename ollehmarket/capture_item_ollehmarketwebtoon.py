#!/usr/bin/env python3

import io
import os
import sys
import re
import getopt
import feedmakerutil


def main():
    displayLimit = 1000
    count = 0
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            displayLimit = int(a)
        
    lineList = feedmakerutil.readStdinAsLineList()
    for line in lineList:
        matches = re.findall(r'"timesseq"\s*:\s*(\d+)[^}]*"webtoonseq"\s*:\s*(\d+)[^}]*"timestitle"\s*:\s*"([^"]+)"', line)
        for match in matches:
            if count > displayLimit:
                break
            timesseq = match[0]
            webtoonseq = match[1]
            link = "http://webtoon.olleh.com/web/times_view.kt?webtoonseq=" + webtoonseq + "&timesseq=" + timesseq
            title = match[2]
            print("%s\t%s" % (link, title))
            count = count + 1

            
if __name__ == "__main__":
	main()

