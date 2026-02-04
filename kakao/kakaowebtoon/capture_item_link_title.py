#!/usr/bin/env python

import sys
import os
import re
import json
import getopt
import logging
import logging.config
from pathlib import Path
from datetime import datetime
from bin.feed_maker_util import IO, URL, Env


logging.config.fileConfig(os.environ["FM_HOME_DIR"] + "/logging.conf")
LOGGER = logging.getLogger()


def compose_description(item, link) -> str:
    description = "<div>\n"
    description += "    <div>%s</div>\n" % item["title"]
    description += "    <div>%s</div>\n" % ", ".join(item["seoKeywords"])
    description += "    <div>%s</div>\n" % item["catchphraseTwoLines"]
    description += "    <div><a href='%s'>%s</a></div>\n" % (link, link)
    description += "    <div><img src='%s'></div>\n" % (item["mergedImage"])
    description += "</div>\n"
    return description


def main() -> int:
    link_prefix = "https://webtoon.kakao.com/content"
    link = ""
    title = ""
    num_of_recent_feeds = 1000

    optlist, _ = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)
        elif o == "-f":
            _ = Path(a)

    content = IO.read_stdin()
    content = re.sub(r'(^(<\S[^>]*>)+|(<\S[^>]*>)+$)', '', content)
    result_list = []
    json_data = json.loads(content)
    if "data" not in json_data:
        return -1
    if "sections" not in json_data["data"]:
        return -1

    for section in json_data["data"]["sections"]:
        # section == weekday
        if "cardGroups" not in section:
            continue
        for card_group in section["cardGroups"]:
            if "cards" not in card_group:
                continue
            for card in card_group["cards"]:
                if "content" not in card:
                    continue

                item = card["content"]

                date_str = "1970-01-01"
                if "serialRestartDateTime" in item and item["serialRestartDateTime"]:
                    date_str = str(datetime.fromisoformat(item["serialRestartDateTime"]).date())
                elif "serialStartDateTime" in item and item["serialStartDateTime"]:
                    date_str = str(datetime.fromisoformat(item["serialStartDateTime"]).date())
                    
                link = "%s/%s/%s" % (link_prefix, item["seoId"], item["id"])
                title = date_str + " " + item["title"]
                if "adult" in item and item["adult"]:
                    title += " (성인)"
                result_list.append((link, title))

                    
    result_list.sort(key=lambda obj: obj[1], reverse=True)
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

    return 0


if __name__ == "__main__":
    sys.exit(main())
