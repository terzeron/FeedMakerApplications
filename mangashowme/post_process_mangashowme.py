#!/usr/bin/env python


import sys
import re
import json
from feedmakerutil import IO


def main():
    for line in IO.read_stdin_as_line_list():
        m = re.search(r'^var img_list = (?P<img_list_str>\[[^\]]+\]);', line)
        if m:
            img_list_str = m.group("img_list_str")
            img_list = json.loads(img_list_str)
            for img in img_list:
                print("<img src='%s' width='100%%'/>" % (img))


if __name__ == "__main__":
    sys.exit(main())
