#!/usr/bin/env python


import sys
import re
import http.client
import feed_maker_util
from feed_maker_util import IO


def main():
    img_host = ""
    img_path = ""
    img_index = -1
    img_ext = "jpg"
    state = 0

    for line in IO.read_stdin_as_line_list():
        line = line.rstrip()
        if re.search(r"<(meta|style)", line):
            print(line)
        else:
            if state == 0:
                m = re.search(r'<a href=\x27(?P<page_url>https?://comic.naver.com/webtoon/list\?titleId=\d+)\x27>', line)
                if m:
                    page_url = m.group("page_url")
                    state = 1
            elif state == 1:
                m = re.search(r"<img src='https?://(?P<img_host>imgcomic.naver.(?:com|net))/(?P<img_path>[^']+_)(?P<img_index>\d+)\.(?P<img_ext>jpg|gif)", line, re.IGNORECASE)
                if m:
                    img_host = m.group("img_host")
                    img_path = m.group("img_path")
                    img_index = int(m.group("img_index"))
                    img_ext = m.group("img_ext")
                    print("<img src='http://%s/%s%d.%s' width='100%%'/>" % (img_host, img_path, img_index, img_ext))
                else:
                    m = re.search(r"<img src='http://(?P<img_host>imgcomic.naver.(?:com|net))/(?P<img_path>[^']+)\.(?P<img_ext>jpg|gif)", line, re.IGNORECASE)
                    if m:
                        img_host = m.group("img_host")
                        img_path = m.group("img_path")
                        img_ext = m.group("img_ext")
                        print("<img src='http://%s/%s.%s' width='100%%'/>" % (img_host, img_path, img_ext))
        
    if img_path != "" and img_index >= 0:
        # add some additional images loaded dynamically
        for i in range(60):
            img_url = "http://%s/%s%d.%s" % (img_host, img_path, i, img_ext)
            cmd = 'wget.sh --spider --referer "%s" "%s"' % (page_url, img_url)
            (result, error) = feed_maker_util.exec_cmd(cmd)
            if not error:
                print("<img src='http://%s/%s%d.%s' width='100%%'/>" % (img_host, img_path, i, img_ext))


if __name__ == "__main__":
    sys.exit(main())
