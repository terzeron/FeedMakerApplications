#!/usr/bin/env python3


import os
import sys
import re
import feedmakerutil


def main():
    state = 0
    
    lineList = feedmakerutil.readStdinAsLineList()
    for line in lineList:
        if state == 0:
            m1 = re.search(r'"path"\s*:\s*"(?P<prefix>[^"]+)"', line)
            if m1:
                prefix = m1.group("prefix")
                state = 1
        elif state == 1:
            m2 = re.search(r'{"name"\s*:\s*"(?P<link>\d[^"]+.md)"}', line)
            if m2:
                link = "http://teamsego.github.io/github-trend-kr/" + prefix + "/" + m2.group("link")
                title = m2.group("link")
                print("%s\t%s" % (link, title))
            m3 = re.search(r'{"volume":', line)
            if m3:
                lineList.insert(0, line)
                state = 0
        #print(state, end=' ')

if __name__ == "__main__":
    main()
