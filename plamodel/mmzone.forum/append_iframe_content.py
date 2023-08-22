#!/usr/bin/env python


import sys
import os
import re
import getopt
import logging
import logging.config
from typing import List, Optional
from bs4 import BeautifulSoup
from bin.feed_maker_util import IO, Process
from bin.crawler import Method, Crawler


logging.config.fileConfig(os.environ["FEED_MAKER_HOME_DIR"] + "/bin/logging.conf")
LOGGER = logging.getLogger()


def process_html(url: str, html: str) -> Optional[str]:
    html = re.sub(r'&nbsp;', ' ', html)
    html = re.sub(r'<!-- ([^>])+ -->', '', html)
    html = re.sub(r'<span[^>]*>', '', html)
    html = re.sub('</span>', '', html)
    html = re.sub(r'<(?P<tag>img|p|div|center)', '\n<\g<tag>', html)
    return html


def main() -> int:
    _, args = getopt.getopt(sys.argv[1:], "f:")
    url = args[0]

    line_list: List[str] = IO.read_stdin_as_line_list()
    for line in line_list:
        if re.search(r'<(meta|style)', line):
            print(line, end='')

    crawler = Crawler(method=Method.GET)

    iframe_url = re.sub(r'mt_view.php', 'inline_content.php', url)
    print(iframe_url)
    response, error, _ = crawler.run(iframe_url)
    if error:
        LOGGER.error(error)
        return 0
    print(process_html(iframe_url, response))

    reply_url = re.sub(r'mt_view.php', 'mms_tool_reply_list.php', url)
    print(reply_url)
    response, error, _ = crawler.run(reply_url)
    if error:
        LOGGER.error(error)
        return 0
    print(process_html(reply_url, response))

    return 0


if __name__ == "__main__":
    sys.exit(main())
