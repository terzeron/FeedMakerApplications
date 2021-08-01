#!/usr/bin/env python

import sys
import os
import re
import json
import getopt
import feed_maker_util
from feed_maker_util import IO, URL, header_str
from feed_maker import FeedMaker


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
                                        description = "<div><span>%s</span>\n<span>%s</span>\n<span>%s</span>\n<span><img src='%s'></span>\n<div>\n" % (item["title"], ", ".join(item["seoKeywords"]), item["catchphraseTwoLines"], item["backgroundImage"] + ".jpg")
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
