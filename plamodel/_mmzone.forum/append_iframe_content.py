#!/usr/bin/env python


import sys
import os
import re
import logging
import logging.config
from typing import List, Optional
from bs4 import BeautifulSoup
from feed_maker_util import IO, exec_cmd
from crawler import Method, Crawler
import download_image


logging.config.fileConfig(os.environ["FEED_MAKER_HOME_DIR"] + "/bin/logging.conf")
LOGGER = logging.getLogger()


def process_html(url: str, html: str) -> Optional[str]:
    html = re.sub('&nbsp;', ' ', html)
    html = re.sub(r'<span[^>]*>', '', html)
    html = re.sub('</span>', '', html)
    html = re.sub(r'<(?P<tag>img|p|div|center)', '\n<\g<tag>', html)
    html, error = exec_cmd("download_image.py '%s'" % url, html)
    if html and not error:
        soup = BeautifulSoup(html, "html.parser")
        return soup.body
    return None
    

def main() -> int:
    url = sys.argv[1]

    line_list: List[str] = IO.read_stdin_as_line_list()
    for line in line_list:
        if re.search(r'<(meta|style)', line):
            print(line, end='')

    iframe_url = re.sub(r'mt_view.php', 'inline_content.php', url)
    crawler = Crawler(method=Method.GET)
    #print(iframe_url)
    html, _ = crawler.run(iframe_url)
    if html:
        print(process_html(iframe_url, html))

    reply_url = re.sub(r'mt_view.php', 'mms_tool_reply_list.php', url)
    #print(reply_url)
    html, _ = crawler.run(reply_url)
    if html:
        print(process_html(reply_url, html))

    return 0


if __name__ == "__main__":
    sys.exit(main())
