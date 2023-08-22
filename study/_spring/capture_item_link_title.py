#!/usr/bin/env python


import sys
import re
import getopt
from bin.feed_maker_util import IO


def main():
    state = 0
    url_prefix = "https://spring.io"
    result_list = []

    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    for line in IO.read_stdin_as_line_list():
        if state == 0:
            if re.search(r'<h2 class="blog--title">', line):
                state = 1
        elif state == 1:
            m = re.search(r'<a href="(?P<link>[^"]+)">(?P<title>.*)</a>', line)
            if m:
                link = url_prefix + m.group("link")
                title = m.group("title")
                if re.search(r'([Bb]ootiful ([Pp]odcast|GCP)|[Aa]vailable|[Rr]eleased|(\d+\.\d+\.\d+(.| )(M\d+|RC\d+|RELEASE)\)?$)|This [Ww]eek|now GA|goes (GA|RC\d+)|is out|SpringOne2GX|[Ww]ebinar|SR\d)', title):
                    state = 0
                    continue
                title = re.sub(r'&amp;', '&', title)
                state = 2
        elif state == 2:
            m = re.search(r'<time class=("|\')date("|\')[^>]*datetime="(?P<date>20\d+-\d+-\d+) ', line)
            if m:
                date = m.group("date")
                title = date + " " + title
                result_list.append((link, title))
                state = 0

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
