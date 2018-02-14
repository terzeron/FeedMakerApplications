#!/usr/bin/env python3


import sys
import re
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
        mobile = m.group("mobile")
        episodeId = m.group("episodeId")
        cmd = ""
        url = ""
        if mobile and mobile == "m/":
            url = "http://cartoon.media.daum.net/data/mobile/webtoon/viewer?id=" + episodeId
        else:
            url = "http://cartoon.media.daum.net/webtoon/viewer_images.js?webtoon_episode_id=" + episodeId
        cmd = "crawler.sh '%s'" % (url)
        #print(cmd)
        (result, error) = feedmakerutil.exec_cmd(cmd)
        #print(result)
        if error:
            print("can't download the page html from '%s'" % (url))
            sys.exit(-1)
        img_file_arr = []
        img_url_arr = []
        img_size_arr = []
        for line in re.split(r"}|\n", result):
            m = re.search(r"\"url\":\"(?P<imgUrl>http://[^\"]+)\",(?:(?:.*imageOrder)|(?:\s*$))", line)
            if m:
                imgUrl = m.group("imgUrl")
                if re.search(r"VodPlayer\.swf", imgUrl):
                    continue
                print("<img src='%s' width='100%%'/>" % (imgUrl))

                        
if __name__ == "__main__":
    sys.exit(main())
