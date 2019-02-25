#!/usr/bin/env python3


import sys
import re
import time
import requests
from typing import Dict, Tuple
import feed_maker_util


def main() -> int:
    url = sys.argv[1]
    webtoon_id: str

    for line in sys.stdin:
        pass

    print(feed_maker_util.header_str)

    m = re.search(r'/(?P<webtoon_id>[^/]+)$', url)
    if m:
        webtoon_id = m.group("webtoon_id")

    if webtoon_id:
        info_url = "http://cartoon.media.daum.net/data/pc/webtoon/view/%s?timeStamp=%d" % (webtoon_id, int(time.time()))
        response = requests.get(info_url, headers={})
        if "data" in response.json():
            print("<div>")
            data = response.json()["data"]
            # 웹툰정보
            if "webtoon" in data:
                webtoon = data["webtoon"]
                if "title" in webtoon:
                    print("<p>제목: %s</p>" % webtoon["title"])
                if "introduction" in webtoon:
                    print("<p>소개: %s</p>" % webtoon["introduction"])
                if "pcHomeImage" in webtoon:
                    if "url" in webtoon["pcHomeImage"]:
                        print("<p><img src='%s'></p>" % webtoon["pcHomeImage"]["url"])
            else:
                return -1

            # 작가정보
            artists_map: Dict[int, Tuple[str, str]] = {}
            if "anotherWebtoons" in data:
                for anotherWebtoon in data["anotherWebtoons"]:
                    if "cartoon" in anotherWebtoon:
                        cartoon = anotherWebtoon["cartoon"]
                        #print(cartoon)
                        if "artists" in cartoon:
                            #print(cartoon["artitsts"])
                            for artist in cartoon["artists"]:
                                order = int(artist["artistOrder"])
                                artists_map[order] = (artist["name"], artist["penName"])
            else:
                return -1                
            for order, info in artists_map.items():
                print("<p>작가: %s (%s)</p>" % (info[0], info[1]))
            print("</div>")
        else:
            return -1    
    return 0


if __name__ == "__main__":
    sys.exit(main())
