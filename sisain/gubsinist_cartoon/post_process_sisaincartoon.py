#!/usr/bin/env python

import sys
import re
import getopt
from pathlib import Path
from bin.feed_maker_util import IO, header_str


def main() -> int:
    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == "-f":
            _ = Path(a)
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
            if re.search(r'<figure class="photo', line):
                print(header_str)
                state = 2
        elif state == 2:
            if re.search(r'<article class="writer">', line):
                state = 3
                break
            m = re.search(r'<img[^>]*src="(?P<img_url>[^"]*)"[^>]*>', line)
            if m:
                img_url = m.group("img_url")
                img_line = f"<img src='{img_url}'>"
                result_list.append(img_line)

    if len(result_list) > 0:
        for line in result_list:
            print(line)
        
    return 0
    

if __name__ == "__main__":
    sys.exit(main())
