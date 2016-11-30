#!/usr/bin/env python3


import sys
import re
import getopt
import feedmakerutil


def main():
    link = ""
    title = ""
    state = 0
    newsUrlPrefix = "http://movie.daum.net/magazine"
    #boonUrlPrefix = "http://1boon.kakao.net/movie"
    boonUrlPrefix = "http://magazine2.movie.daum.net/movie"

    numOfRecentFeeds = 30
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    resultList = []
    lineList = feedmakerutil.readStdinAsLineList()
    for line in lineList:
        if state == 0:
            m = re.search(r'<a href="(?P<url>[^"]+)" class="link_magazine', line)
            if m:
                link = m.group("url")
                if re.search(r'news/article\?newsId=', link):
                    link = newsUrlPrefix + "/" + link
                else:
                    m = re.search(r"javascript:show1BoonContents\('(?P<articleId>\d+)'\s*,\s*\d+\)", link)
                    if m:
                        link = boonUrlPrefix + "/" + m.group("articleId")
                state = 1
        elif state == 1:
            m = re.search(r'<strong class="tit_magazine">(?P<title>[^<]*)</strong>', line)
            if m:
                title = m.group("title")
                if re.search(r'^\[사진\]', title):
                    continue
                if link and title:
                    resultList.append((link, title))
                state = 0
                
    for (link, title) in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))
                

if __name__ == "__main__":
    main()
