#!/usr/bin/env python


import sys
import re
import json
from typing import List
from feed_maker_util import IO


def main() -> int:
    line_list: List[str] = IO.read_stdin_as_line_list()
    for line in line_list:
        m = re.search(r'var\s+img_list\d*\s*=\s*(?P<img_list>\[.*\])', line)
        if m:
            img_list_str = re.sub(r'\\/', '/', m.group("img_list"))
            if json.loads(img_list_str):
                img_list = json.loads(img_list_str)

    for img in img_list:
        print("<img src='%s'/>" % img)

    return 0


if __name__ == "__main__":
    sys.exit(main())
