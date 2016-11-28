#!/usr/bin/env python3


import sys
import re
import feedmakerutil

    
def main():
    link = ""
    urlPrefix = "http://navercast.naver.com/"
    title = ""
    state = 0

    for line in feedmakerutil.readStdinAsLineList():
        if state == 0:
            m = re.search(r'<a class="card" href="/?(?P<url>contents\.nhn\?contents_id=\d+[^"]*)"[^>]*>', line)
            if m:
                url = m.group("url")
                url = re.sub(r"&amp;", "&", url)
                link = urlPrefix + url
                state = 1
        elif state == 1:
            m = re.search(r'<strong>(?P<mainTitle>[^<]+)</strong><span(?: alt="[^"]+" title="(?P<subTitle1>[^"]+)")?>(?P<subTitle2>.*)</span>', line)
            if m:
                if m.group("subTitle1"):
                    title = m.group("mainTitle") + " - " + m.group("subTitle1")
                else:
                    title = m.group("mainTitle") + " - " + m.group("subTitle2")
                print("%s\t%s" % (link, title))
                state = 0
                link = ""
                title = ""


if __name__ == "__main__":
    sys.exit(main())
