#!/usr/bin/env python

import sys
import re
import base64
from bs4 import BeautifulSoup
from bin.feed_maker_util import IO, URL, header_str


def main():
    url_prefix = ""

    print(header_str)

    state = 0
    for line in IO.read_stdin_as_line_list():
        if state == 0:
            m = re.search(r'<img class="lazy-read"', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(r'data-original="(?P<img_url>[^"]+)"', line)
            if m:
                img_url = m.group("img_url")
                print(f"<img src='{img_url}' />")
                state = 0
                

if __name__ == "__main__":
    sys.exit(main())
