#!/usr/bin/env python


import sys
import re
import json
import feed_maker_util
from feed_maker_util import IO
from crawler import Method, Crawler


def main():
    img_prefix = ""
    img_index = -1
    img_ext = "jpg"
    num_units = 25

    for line in IO.read_stdin_as_line_list():
        line = line.rstrip()
        m = re.search(r"^<img src", line)
        if not m:
            print(line)

    post_link = sys.argv[1]
    m = re.search(r"http://cartoon\.media\.daum\.net/(?P<mobile>m/)?webtoon/viewer/(?P<episode_id>\d+)$", post_link)
    if m:
        episode_id = m.group("episode_id")
        cmd = ""
        url = "http://webtoon.daum.net/data/pc/webtoon/viewer_images/" + episode_id
        crawler = Crawler()
        result = crawler.run(url)
        if not result:
            print("can't download the page html from '%s'" % (url))
            sys.exit(-1)
        img_file_arr = []
        img_url_arr = []
        img_size_arr = []
        try:
            content = json.loads(result)
        except json.decoder.JSONDecodeError:
            #print(cmd)
            #print(result)
            raise json.decoder.JSONDecodeError

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
