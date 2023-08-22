#!/usr/bin/env python

import sys
import re
from bin.feed_maker_util import IO


def main():
    secondPageUrl = ""
    imgUrlList = []

    for line in IO.read_stdin_as_line_list():
        line = line.rstrip()
        m = re.search(r"<img src='(?P<imgUrl>http://comicmenu.mt.co.kr/[^']+.jpg)'(?: width='\d+%')?/>", line)
        if m:
            imgUrl = m.group("imgUrl")
            # 광고 이미지 skip
            if re.search(r"http://comicmenu.mt.co.kr/banner/comic_\d+_100811.jpg", imgUrl):
                continue
            imgUrlList.append(imgUrl)

        m = re.search(r"<a href='(?P<secondPageUrl>http://[^']+)'[^>]*>", line)
        if m:
            secondPageUrl = m.group("secondPageUrl")
        else:
            m = re.search(r"<img src='http://comicmenu\.mt\.co\.kr/images/btn_cartoon_2p\.gif'/>", line)
            if m:
                break

    # 마지막 광고 이미지 제거
    imgUrlList.pop()
            
    if secondPageUrl != "":
        cmd = "wget.sh '%s' | extract.py '%s'" % (secondPageUrl, sys.argv[1])
        (result, error) = feed_maker_util.exec_cmd(cmd)
        for line in result.split("\n"):
            m = re.search(r"<img src='(?P<imgUrl>http://comicmenu.mt.co.kr/[^']+.jpg)'(?: width='\d+%')?/>", line)
            if m:
                imgUrl = m.group("imgUrl")
                if re.search(r"http://comicmenu.mt.co.kr/banner/comic_\d+_100811.jpg", imgUrl):
                    continue
                imgUrlList.append(imgUrl)

    for imgUrl in imgUrlList:
        print("<img src='%s' width='100%%'/>" % (imgUrl))

        
if __name__ == "__main__":
    sys.exit(main())
