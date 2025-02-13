#!/usr/bin/env python


import sys
import json
import getopt
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    url_prefix = "https://comic.naver.com/webtoon/list?titleId="
    result_list = []

    num_of_recent_feeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    content = IO.read_stdin()
    json_data = json.loads(content)

    if "titleList" in json_data:
        for data_item in json_data["titleList"]:
            if "titleId" in data_item:
                title_id = data_item["titleId"]
                link = url_prefix + str(title_id)
            if "titleName" in data_item:
                title = data_item["titleName"]
                if "adult" in data_item and data_item["adult"]:
                    title += " (성인)"
                result_list.append((link, title))

    result_list.sort(key=lambda obj: int(obj[0].split("=")[1]), reverse=True)
    for link, title in result_list[:num_of_recent_feeds]:
        print(f"{link}\t{title}")
                    
            
if __name__ == "__main__":
    sys.exit(main())
