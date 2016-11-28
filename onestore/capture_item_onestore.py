#!/usr/bin/env python3


import sys
import re
import feedmakerutil


def main():
    link = ""
    title = ""
    urlPrefix = "http://m.tstore.co.kr/mobilepoc/webtoon/webtoonDetail.omp?prodId="

    for line in feedmakerutil.readStdinAsLineList():
        matches = re.findall(r'''
        [^}]*,
        "prodId"\s*:\s*"\s*([^"]+)\s*",
        [^}]*,
        "prodNm"\s*:\s*"\s*([^"]+)\s*",
        ''', line, re.VERBOSE)
        for match in matches:
            link = urlPrefix + match[0]
            title = match[1]
            print("%s\t%s" % (link, title))
            

if __name__ == "__main__":
    sys.exit(main())
