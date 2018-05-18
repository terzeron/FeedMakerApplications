#!/usr/bin/env python3


import sys
import re
import json
import feedmakerutil
from feedmakerutil import IO


def main():
    imgPrefix = ""
    imgIndex = -1
    imgExt = "jpg"
    numUnits = 25

    for line in IO.read_stdin_as_line_list():
        line = line.rstrip()
        print(line)

    postLink = sys.argv[1]
    m = re.search(r"http://cartoon\.media\.daum\.net/(?P<mobile>m/)?webtoon/viewer/(?P<episodeId>\d+)$", postLink)
    if m:
        episodeId = m.group("episodeId")
        cmd = ""
        url = "http://webtoon.daum.net/data/pc/webtoon/viewer_images/" + episodeId
        cmd = "crawler.py '%s'" % (url)
        #print(cmd)
        (result, error) = feedmakerutil.exec_cmd(cmd)
        #print(result)
        if error:
            print("can't download the page html from '%s'" % (url))
            sys.exit(-1)
        img_file_arr = []
        img_url_arr = []
        img_size_arr = []
        content = json.loads(result)
        if "data" in content:
            if content["data"]:
                for item in content["data"]:
                    if "url" in item:
                        img_url = item["url"]
                        if re.search(r"VodPlayer\.swf", img_url):
                            continue
                        print("<img src='%s' width='100%%'/>" % (img_url))

                        
if __name__ == "__main__":
    sys.exit(main())
