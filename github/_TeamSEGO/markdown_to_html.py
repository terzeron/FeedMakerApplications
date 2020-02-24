#!/usr/bin/env python


import os
import sys
import re
import feed_maker_util


def main(url):
    cmd = "markdown"
    (html, error) = feed_maker_util.exec_cmd(cmd)
    for line in html.split("\n"):
        m = re.search(r'https?://[^\"\'\<\>\)\(]+', line)
        if m:
            if not re.search(r'<(a|img)[^>]*(href|src)=[\"\'](https?://[^\"\']*)', line):
                line = "<a href='" + m.group(0) + "'>" + m.group(0) + "</a>"
        print(line)
    

if __name__ == "__main__":
    main(sys.argv[1])
