#!/usr/bin/env python

import sys
import re
import base64
from bs4 import BeautifulSoup
from bin.feed_maker_util import IO, URL


def main():
    url_prefix = ""
    state = 0
    
    for line in IO.read_stdin_as_line_list():
        if state == 0:
            m = re.search(r'<meta property="og:url" content="(?P<url_prefix>http[^"]+)"', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'var toon_img\s*=\s*\x27(?P<str>[^\x27]+)\x27', line)
            if m:
                str = m.group("str")
                html = base64.b64decode(str).decode("utf-8")
                soup = BeautifulSoup(html, "html.parser")
                for img in soup.find_all("img"):
                    img_url = URL.concatenate_url(url_prefix, img["src"])
                    print(f"<img src='{img_url}' />")


if __name__ == "__main__":
    sys.exit(main())
