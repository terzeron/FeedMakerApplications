#!/usr/bin/env python


import sys
import re
import json
import pprint
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    state = 0
    url_prefix = "http://comic.naver.com/webtoon/list?titleId="
    result_list = []

    content = IO.read_stdin()
    json_data = json.loads(content)
    if "titleListMap" in json_data:
        for _, data_list in json_data["titleListMap"].items():
            for data_item in data_list:
                if not data_item["adult"]:
                    if "titleId" in data_item:
                        title_id = data_item["titleId"]
                        link = url_prefix + str(title_id)
                    if "titleName" in data_item:
                        title = data_item["titleName"]
                        result_list.append((link, title))

    for link, title in result_list:
        print(f"{link}\t{title}")
                    
            
if __name__ == "__main__":
    sys.exit(main())
