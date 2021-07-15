#!/usr/bin/env python


import sys
import os
import logging
import logging.config
from typing import List
from feed_maker_util import IO, exec_cmd


logging.config.fileConfig(os.environ["FEED_MAKER_HOME_DIR"] + "/bin/logging.conf")
LOGGER = logging.getLogger()


def main() -> int:
    exclude_keywords = ["로맨스", "연인", "연애", "키스", "짝사랑", "고백", "유부녀", "황후", "왕후", "왕비", "공녀", "첫사랑", "재벌", "순정", "후궁", "로판", "로맨스판타지", "멜로"]
    line_list: List[str] = IO.read_stdin_as_line_list()
    for line in line_list:
        for exclude_keyword in exclude_keywords:
            if exclude_keyword in line:
                print("<div>문장: %s</div>\n" % line)
                print("<div>제외어: %s</div>\n" % exclude_keyword)
                return 0

    for line in line_list:
        print(line, end='')

    return 0


if __name__ == "__main__":
    sys.exit(main())
