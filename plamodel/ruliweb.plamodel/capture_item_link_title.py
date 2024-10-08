#!/usr/bin/env python


import sys
import re
import getopt
from bin.feed_maker_util import IO


def main():
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    keyword_exclusion_list = ["가면라이더", "헥사기어", "Warhammer", "워해머", "아수라", "키즈나", "메가미", "카나메", "반간", "다간", "리베르 나이트", "창채소녀", "판타지 포레스트", "리벨 나이트", "루나마리아", "FRS", "젠레스", "니콜 데마라"]

    state = 0
    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        if state == 0:
            m = re.search(r'class="subject"', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(r'<a class="deco" href="(?P<link>[^\?"]+)[^"]*">\s*(?:<strong>)?\s*(?P<title>\S.+\S)\s*(?:</strong>)?\s*</a>', line)
            if m:
                link = m.group("link")
                link = re.sub(r'&amp;', '&', link)
                title = m.group("title")
                state = 2
                for keyword in keyword_exclusion_list:
                    if keyword in title:
                        state = 0
                        break
        elif state == 2:
            m = re.search(r'class="writer', line)
            if m:
                state = 3
        elif state == 3:
            m = re.search(r'<a[^>]*>(?P<author>.+)</a>', line)
            if m:
                author = m.group("author")
                title = title + " | " + author
                result_list.append((link, title))
                state = 0

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
