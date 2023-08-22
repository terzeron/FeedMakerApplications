#!/usr/bin/env python

import sys
import os
import re
import json
import getopt
from typing import List
import logging
import logging.config
from pathlib import Path
from bin.feed_maker_util import IO, URL, header_str
from bin.feed_maker import FeedMaker


logging.config.fileConfig(os.environ["FEED_MAKER_HOME_DIR"] + "/bin/logging.conf")
LOGGER = logging.getLogger()


def check_excluded_keyword(line_list: List[str]):
    excluded_keyword_list = ["남장여자", "에로틱", "로맨스", "육아"]
    for excluded_keyword in excluded_keyword_list:
        for line in line_list:
            if excluded_keyword in line:
                return True
    return False


def compose_description(item, link):
    description = "<div>\n"
    description += "    <div>%s</div>\n" % item["title"]
    description += "    <div>%s</div>\n" % ", ".join(item["seoKeywords"])
    description += "    <div>%s</div>\n" % item["catchphraseTwoLines"]
    description += "    <div><a href='%s'>%s</a></div>\n" % (link, link)
    description += "    <div class='position: relative;'>\n"
    description += "        <div style='position: absolute; top: 150px; max-height: 600px; overflow: hidden;'><img src='%s'></div>\n" % (item["backgroundImage"] + ".webp")
    description += "        <div style='position: absolute; top: 150px;'><img src='%s'></div>\n" % (item["featuredCharacterImageA"] + ".png")
    description += "    </div>\n"
    description += "</div>\n"
    return description


def main():
    link_prefix = "http://webtoon.kakao.com/content"
    link = ""
    title = ""
    num_of_recent_feeds = 1000
    feed_dir_path = Path.cwd()

    optlist, _ = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)
        elif o == "-f":
            feed_dir_path = Path(a)

    content = IO.read_stdin()
    content = re.sub(r'(^(<\S[^>]*>)+|(<\S[^>]*>)+$)', '', content)
    result_list = []
    json_data = json.loads(content)
    if "data" in json_data:
        if "sections" in json_data["data"]: 
            for section in json_data["data"]["sections"]:
                # section == weekday
                if "cardGroups" in section:
                    for card_group in section["cardGroups"]:
                        if "cards" in card_group:
                            for card in card_group["cards"]:
                                if "content" in card:
                                    item = card["content"]
                                    if not item["adult"] and not check_excluded_keyword(item["seoKeywords"]):
                                        link = "%s/%s/%s" % (link_prefix, item["seoId"], item["id"])
                                        title = item["title"]
                                        result_list.append((link, title))

                                        # 특수한 처리 - extraction 단계를 여기서 수행
                                        description = compose_description(item, link)
                                        html_file_name = URL.get_short_md5_name(URL.get_url_path(link)) + ".html"
                                        file_path = feed_dir_path / "html" / html_file_name

                                        if os.path.isfile(file_path):
                                            continue
                                        with open(file_path, 'w', encoding="utf-8") as fp:
                                            fp.write(header_str)
                                            fp.write(description)
                                            fp.write(FeedMaker.get_image_tag_str("https://terzeron.com", "kakaowebtoon.xml", link))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
