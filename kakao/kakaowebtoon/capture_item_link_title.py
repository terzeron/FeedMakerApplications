#!/usr/bin/env python

import sys
import os
import re
import json
import getopt
import logging.config
from typing import List
import feed_maker_util
from feed_maker_util import IO, URL, header_str
from feed_maker import FeedMaker


logging.config.fileConfig(os.environ["FEED_MAKER_HOME_DIR"] + "/bin/logging.conf")
LOGGER = logging.getLogger(__name__)
exclude_keywords: List[str] = ["로맨스", "연인", "연애", "키스", "짝사랑", "고백", "유부녀", "황후", "왕후", "왕비", "공녀", "첫사랑", "재벌", "순정", "후궁", "로판", "로맨스판타지", "멜로"]


def exclude_keyword_filter(text: str) -> bool:
    for exclude_keyword in exclude_keywords:
        if exclude_keyword in text:
            return True
    return False


def main():
    link_prefix = "http://webtoon.kakao.com/content"
    link = ""
    title = ""

    num_of_recent_feeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    content = IO.read_stdin()
    content = re.sub(r'(^(<\S[^>]*>)+|(<\S[^>]*>)+$)', '', content)
    result_list = []
    json_data = json.loads(content)
    if "data" in json_data:
        if "sections" in json_data["data"]:
            for section in json_data["data"]["sections"]:
                if "cardGroups" in section:
                    for card_group in section["cardGroups"]:
                        if "cards" in card_group:
                            for card in card_group["cards"]:
                                if "content" in card:
                                    item = card["content"]
                                    if not item["adult"]:
                                        link = "%s/%s/%s" % (link_prefix, item["seoId"], item["id"])
                                        title = item["title"]
                                        result_list.append((link, title))
                    
                                        # 특수한 처리 - extraction 단계를 여기서 수행
                                        description = "<div>\n"
                                        description += "    <div>%s</div>\n" % item["title"]
                                        if exclude_keyword_filter(", ".join(item["seoKeywords"])):
                                            continue
                                        description += "    <div>%s</div>\n" % ", ".join(item["seoKeywords"])
                                        description += "    <div>%s</div>\n" % item["catchphraseTwoLines"]
                                        description += "    <div><a href='%s'>%s</a></div>\n" % (link, link)
                                        description += "    <div class='position: relative;'>\n"
                                        description += "        <div style='position: absolute; top: 150px; max-height: 600px; overflow: hidden;'><img src='%s'></div>\n" % (item["backgroundImage"] + ".webp")
                                        description += "        <div style='position: absolute; top: 150px;'><img src='%s'></div>\n" % (item["featuredCharacterImageA"] + ".png")
                                        description += "    </div>\n"
                                        description += "</div>\n"
                                        file_path = os.path.join("html", URL.get_short_md5_name(URL.get_url_path(link)) + ".html")

                                        if os.path.isfile(file_path):
                                            continue
                                        with open(file_path, 'w') as fp:
                                            fp.write(header_str)
                                            fp.write(description)
                                            fp.write(FeedMaker.get_image_tag_str("kakaowebtoon.xml", link))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))
                

if __name__ == "__main__":
    sys.exit(main())
