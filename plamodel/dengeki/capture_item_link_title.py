#!/usr/bin/env python


import sys
import re
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO
from utils.translation import Translation


def main():
    num_of_recent_feeds = 1000
    do_translate = False
    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:t")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)
        elif o == '-t':
            do_translate = True

    content = IO.read_stdin()
    result_list = []

    # id="contents" 영역만 추출
    contents_match = re.search(r'<div id="contents"[^>]*>(.*?)</main>', content, re.DOTALL)
    if contents_match:
        contents_area = contents_match.group(1)

        # h2 또는 h3 태그 안의 링크와 제목 추출
        for m in re.finditer(r'<h[23]><a href="(?P<link>[^"]+)"[^>]*>(?P<title>[^<]+)</a></h[23]>', contents_area):
            link = m.group("link")
            title = m.group("title").strip()
            result_list.append((link, title))

    if do_translate:
        translation = Translation()
        result_list = translation.translate(result_list[:num_of_recent_feeds])

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
