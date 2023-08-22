#!/usr/bin/env python


import sys
import os
import re
import getopt
import json
import logging
import logging.config
from typing import List
from pathlib import Path
import feed_maker_util
from bin.crawler import Crawler, Method


logging.config.fileConfig(os.environ["FEED_MAKER_HOME_DIR"] + "/bin/logging.conf")
LOGGER = logging.getLogger(__name__)
excluded_keywords: List[str] = ["로맨스", "연인", "연애", "키스", "짝사랑", "고백", "유부녀", "황후", "왕후", "왕비", "공녀", "첫사랑", "재벌", "순정", "후궁", "로판", "로맨스판타지", "멜로"]


def excluded_keyword_filter(text: str) -> str:
    for excluded_keyword in excluded_keywords:
        if excluded_keyword in text:
            return excluded_keyword
    return ""


def main() -> int:
    feed_dir_path = Path.cwd()
    series_id: str = ""
    content: str = ""

    optlist, args = getopt.getopt(sys.argv[1:], "f:")
    for o, a in optlist:
        if o == "-f":
            feed_dir_path = Path(a)    

    for _ in sys.stdin:
        pass

    url = args[0]

    m = re.search(r'seriesId=(?P<series_id>\d+)', url)
    if m:
        series_id = m.group("series_id")
    if not series_id:
        return -1

    info_url = "https://api2-page.kakao.com/api/v4/store/seriesdetail?seriesid=" + series_id
    crawler = Crawler(dir_path=feed_dir_path, render_js=False, method=Method.POST)
    result, error, _ = crawler.run(info_url)
    if error:
        LOGGER.error(f"Error: can't get data from '{info_url}'")
        return -1
    data = json.loads(result)
    content += feed_maker_util.header_str
    content += "<div>\n"
    if "seriesdetail" in data:
        detail = data["seriesdetail"]
        if "title" in detail:
            excluded_keyword = excluded_keyword_filter(detail["title"])
            if excluded_keyword:
                print("<p>제외어: %s</p>\n" % excluded_keyword)
                return 0
            content += "<p>제목: %s</p>\n" % detail["title"]
        if "author_name" in detail["author_name"]:
            content += "<p>작가: %s</p>\n" % detail["author_name"]
        if "description" in detail:
            excluded_keyword = excluded_keyword_filter(detail["description"])
            if excluded_keyword:
                print("<p>제외어: %s</p>\n" % excluded_keyword)
                return 0
            content += "<p>소개: %s</p>\n" % detail["description"]
        if "category" in detail:
            excluded_keyword = excluded_keyword_filter(detail["category"])
            if excluded_keyword:
                print("<p>제외어: %s</p>\n" % excluded_keyword)
                return 0
            content += "<p>장르: %s</p>\n" % detail["category"]
        if "sub_category" in detail:
            excluded_keyword = excluded_keyword_filter(detail["sub_category"])
            if excluded_keyword:
                print("<p>제외어: %s</p>\n" % excluded_keyword)
                return 0
            content += "<p>장르: %s</p>\n" % detail["sub_category"]
    if "authors_other" in data:
        for item in data["authors_other"]:
            if "land_thumbnail_url" in item:
                content += "<p><img src='%s'></p>\n" % ("https://dn-img-page.kakao.com/download/resource?kid=" + item["land_thumbnail_url"])
    content += "</div>\n"

    print(content)

    return 0


if __name__ == "__main__":
    sys.exit(main())
