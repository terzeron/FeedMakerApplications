#!/usr/bin/env python


import sys
import re
import urllib.parse
from bin.feed_maker_util import IO


def main():
    url: str = None
    title: str = None
    url_format: str = "http://bookdb.co.kr/bdb/SeriesOfArtists.do?_method=NovelDetailByAuthor&sc.themeNo=%d&sc.webzNo=%d"
    state: int = 0
    theme_no: int = 0

    result_list = []
    for line in IO.read_stdin_as_line_list():
        if state == 0:
            if re.search(r'gotoListOrderSelect\(', line):
                state = 1
        elif state == 1:
            m = re.search(r'location\.href="/meet/webZineDiary\.do\?_method=novelListByAuthor&sc.contsType=\d+&sc.contsDtlType=\d+&sc.themeNo=(?P<theme_no>\d+)&', line)
            if m:
                theme_no = int(m.group("theme_no"))
                state = 2
        elif state == 2:
            m = re.search(r'<td><p><a href="javascript:toContent\((?P<article_no>\d+)\.\d+\);">(?P<title>.*)</a></p></td>', line)
            if m:
                article_no = int(m.group("article_no"))
                title = m.group("title")
                url = url_format % (theme_no, article_no)
                result_list.append((url, title))

    for url, title in result_list:
        print("%s\t%s" % (url, title))
            

if __name__ == "__main__":
    sys.exit(main())
