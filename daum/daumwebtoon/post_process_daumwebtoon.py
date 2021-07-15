#!/usr/bin/env python


import sys
import re
import time
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
    webtoon_id: str = ""
    content: str = ""

    for _ in sys.stdin:
        pass

    content += feed_maker_util.header_str

    m = re.search(r'/(?P<webtoon_id>[^/]+)$', url)
    if m:
        webtoon_id = m.group("webtoon_id")

    if not webtoon_id:
        return -1

    info_url = "http://cartoon.media.daum.net/data/pc/webtoon/view/%s?timeStamp=%d" % (webtoon_id, int(time.time()))
    response = requests.get(info_url, headers={})
    if "data" in response.json():
        content += "<div>\n"
        data = response.json()["data"]
        # 웹툰정보
        if "webtoon" not in data:
            return -1
        webtoon = data["webtoon"]
        if "title" in webtoon:
            if exclude_keyword_filter(webtoon["title"]):
                return 0
            content += "<p>제목: %s</p>\n" % webtoon["title"]
        if "pcHomeImage" in webtoon:
            if "url" in webtoon["pcHomeImage"]:
                content += "<p><img src='%s'></p>\n" % webtoon["pcHomeImage"]["url"]
        if "introduction" in webtoon:
            if exclude_keyword_filter(webtoon["introduction"]):
                return 0
            content += "<p>소개: %s</p>\n" % webtoon["introduction"]
        if "cartoon" in webtoon:
            cartoon = webtoon["cartoon"]
            if "genres" in cartoon:
                for genre in cartoon["genres"]:
                    if exclude_keyword_filter(genre["name"]):
                        return 0
                    content += "<p>장르: %s</p>\n" % genre["name"]
            if "artists" in webtoon["cartoon"]:
                for artist in cartoon["artists"]:
                    content += "<p>작가: %s (%s)</p>\n" % (artist["penName"], artist["name"])
            if "categories" in cartoon:
                for category in cartoon["categories"]:
                    if exclude_keyword_filter(category["name"]):
                        return 0
        content += "</div>\n"

    print(content)

    return 0


if __name__ == "__main__":
    sys.exit(main())
