#!/usr/bin/env python3


import io
import os
import sys
import re
import json
from feedmakerutil import IO


def main():
    link_prefix = "http://cartoon.media.daum.net/webtoon/view/"

    json_str = IO.read_stdin()
    json_obj = json.loads(json_str)
    for item in json_obj["data"]:
        link = link_prefix + item["nickname"]
        title = item["title"]
        if item["ageGrade"] == 0:
            print("%s\t%s" % (link, title))
        
            
if __name__ == "__main__":
    main()
        
