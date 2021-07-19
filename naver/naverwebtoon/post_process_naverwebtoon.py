#!/usr/bin/env python


import sys
import os
import re
import logging
import logging.config
from typing import List
from feed_maker_util import IO, exec_cmd, Config, URL


logging.config.fileConfig(os.environ["FEED_MAKER_HOME_DIR"] + "/bin/logging.conf")
LOGGER = logging.getLogger()


def main() -> int:
    exclude_keywords = ["로맨스", "연인", "연애", "키스", "짝사랑", "고백", "유부녀", "황후", "왕후", "왕비", "공녀", "첫사랑", "재벌", "순정", "후궁", "로판", "로맨스판타지", "멜로"]
    line_list: List[str] = IO.read_stdin_as_line_list()
    for line in line_list:
        for exclude_keyword in exclude_keywords:
            if exclude_keyword in line:
                #print("<div>문장: %s</div>\n" % line)
                print("<p>제외어: %s</p>\n" % exclude_keyword)
                config = Config()
                if not config:
                    LOGGER.error("can't read configuration")
                    return -1
                rss_conf = config.get_rss_configs()
                link = rss_conf["rss_link"]
                m = re.search(r'\/(?P<rss_file_name>\S+\.xml)', link)
                if m:
                    rss_file_name = m.group("rss_file_name")
                url = sys.argv[1]
                md5_name = URL.get_short_md5_name(URL.get_url_path(url))
                print("<img src='https://terzeron.com/img/1x1.jpg?feed=%s&item=%s'/>" % (rss_file_name, md5_name))
                return 0

    for line in line_list:
        print(line, end='')

    return 0


if __name__ == "__main__":
    sys.exit(main())
