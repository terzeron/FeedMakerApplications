#!/usr/bin/env python

import sys
import re
import getopt
import base64
from pathlib import Path
from bs4 import BeautifulSoup
from bin.feed_maker_util import IO, URL


def main() -> int:
    optlist, args = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == "-f":
            feed_dir_path = Path(a)
        if o == "-n":
            _ = int(a)

    result_list = []
    state = 0
    for line in IO.read_stdin_as_line_list():
        if state == 0:
            m = re.search(r'<article[^>]*id="article-view-content-div"', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(r'<figure class="photo', line)
            if m:
                result_list.append(line)
            m = re.search(r'<div class="press">', line)
            if m:
                break

    if len(result_list) > 1:
        for line in result_list:
            print(line)
        
    return 0
    

if __name__ == "__main__":
    sys.exit(main())
