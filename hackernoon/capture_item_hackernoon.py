#!/usr/bin/env python


import sys
import re
import getopt
from pathlib import Path
from bin.feed_maker_util import IO


def main():
    num_of_recent_feeds = 1000
    feed_dir_path = Path.cwd()

    optlist, _ = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)
        elif o == "-f":
            feed_dir_path = Path(a)
    
    state = 0
    url_prefix = "https://hackernoon.com"
    result_list = []
    for chunk in IO.read_stdin_as_line_list():
        for line in re.split(r'(?<=>)', chunk):
            if state == 0:
                m = re.search(r'<div class="title-wrapper">', line)
                if m:
                    state = 1
            elif state == 1:
                m = re.search(r'<a href="(?P<link>[^"]+)"', line)
                if m:
                    link = m.group("link")
                    if link.startswith("http"):
                        state = 0
                        continue
                    link = url_prefix + link
                    state = 2
            elif state == 2:
                m = re.search(r'(?P<title>[^<]+)</a>', line)
                if m:
                    title = m.group("title")
                    result_list.append((link, title))
                    state = 0

    for link, title in result_list[:num_of_recent_feeds]:
        print(f"{link}\t{title}")

        
if __name__ == "__main__":
    sys.exit(main())
