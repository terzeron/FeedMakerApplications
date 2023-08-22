#!/usr/bin/env python


import sys
import re
import getopt
from bin.feed_maker_util import IO


def main():
    urlPrefix = "http://sports.media.daum.net/sports/column/newsview?newsId="
    link = ""
    title = ""
    state = 0

    numOfRecentFeeds = 30
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    resultList = []
    lineList = IO.read_stdin_as_line_list()
    # html 파일에서 데이터 꺼내기
    for line in lineList:
        if state == 0:
            m = re.search(r'<a href="/sports/column/newsview\?newsId=(?P<newsId>\d+)&mccid=\d+" class="link_thumb">', line)
            if m:
                link = urlPrefix + m.group("newsId")
                state = 1
        elif state == 1:
            m = re.search(r'<strong class="tit_thumb">\s*(?P<title>\S[^<]*\S)\s*</strong>', line)
            if m:
                title = m.group("title")
                if link and title:
                    resultList.append((link, title))
                state = 0

    # json 파일에서 데이터 꺼내기
    for line in lineList:
        matches = re.findall(r'"key"\s*:\s*"(\d+)"[^{]*"title"\s*:\s*"(.+?)",', line)
        for match in matches:
            link = urlPrefix + match[0]
            title = match[1]
            resultList.append((link, title))

    for (link, title) in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))
                

if __name__ == "__main__":
    main()
