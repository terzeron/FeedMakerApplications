#!/usr/bin/env python


import sys
import re
from typing import List
import requests
import feed_maker_util


exclude_keywords: List[str] = ["로맨스", "연인", "연애", "키스", "짝사랑", "고백", "유부녀", "황후", "왕후", "왕비", "공녀", "첫사랑", "재벌", "순정", "후궁", "로판", "로맨스판타지", "멜로"]


def exclude_keyword_filter(text: str) -> bool:
    for exclude_keyword in exclude_keywords:
        if exclude_keyword in text:
            return True
    return False


def main() -> int:
    url = sys.argv[1]
    series_id: str = ""
    content: str = ""

    for _ in sys.stdin:
        pass

    content += feed_maker_util.header_str

    m = re.search(r'seriesId=(?P<series_id>\d+)', url)
    if m:
        series_id = m.group("series_id")

    if not series_id:
        return -1

    info_url = "https://api2-page.kakao.com/api/v4/store/seriesdetail?seriesid=" + series_id
    response = requests.post(info_url, headers={})

    data = response.json()
    content += "<div>\n"
    if "seriesdetail" in data:
        detail = data["seriesdetail"]
        if "title" in detail:
            if exclude_keyword_filter(detail["title"]):
                return 0
            content += "<p>제목: %s</p>\n" % detail["title"]
        if "author_name" in detail["author_name"]:
            content += "<p>작가: %s</p>\n" % detail["author_name"]
        if "description" in detail:
            if exclude_keyword_filter(detail["description"]):
                return 0
            content += "<p>소개: %s</p>\n" % detail["description"]
        if "category" in detail:
            if exclude_keyword_filter(detail["category"]):
                return 0
            content += "<p>장르: %s</p>\n" % detail["category"]
        if "sub_category" in detail:
            if exclude_keyword_filter(detail["sub_category"]):
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
