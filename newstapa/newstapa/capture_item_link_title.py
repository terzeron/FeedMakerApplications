#!/usr/bin/env python3


import os
import sys
import re
import getopt
from feed_maker_util import IO


def main():
    link_prefix = "https://newstapa.org"
    
    num_of_recent_feeds = 10
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)
    
    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        matches = re.findall(r'<a href="/article/[^"]+"><img[^>]*src="https://[^"]*?/(?P<year>\d+)/(?P<month>\d+)/(?P<id>..)[^"]*"/>.*?<a href="(?P<link>/article/[^"]+)">(?P<title>[^<]+)</a>', line)
        for match in matches:
            article_id = "%s%s%03d" % (match[0], match[1], int(match[2], 16))
            link = link_prefix + match[3]
            title = match[4]
            result_list.append((link, title, article_id))

    for (link, title, article_id) in result_list[:num_of_recent_feeds]:
        print("%s\t%s. %s" % (link, article_id, title))

        
if __name__ == "__main__":
    sys.exit(main())
