#!/usr/bin/env python

import sys
import re
import getopt
import json
from bin.feed_maker_util import IO


def main():
    url_prefix = "http://m.post.naver.com"
    link = ""
    title = ""

    num_of_recent_feeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    content = "".join(line_list)
    content = re.sub(r'\\\'', '\'', content)
    data = json.loads(content)
    if "html" in data:
        state = 0
        result_list = []
        for line in data["html"].split("\n"):
            if state == 0:
                m = re.search(r'<a href="(?P<url>/viewer/postView\.naver\?volumeNo=\d+&memberNo=\d+)"', line)
                if m:
                    url = m.group("url")
                    url = re.sub(r'&lt;', '<', url)
                    url = re.sub(r'&gt;', '>', url)
                    link = url_prefix + url
                    title = ""
                    state = 1
            elif state == 1:
                if re.search(r'class="link_end"', line):
                    state = 2
                else:
                    state = 0
            elif state == 2:
                if re.search(r'<h3 class="tit_feed', line):
                    state = 3
                else:
                    if re.search(r'<strong class="tit_feed', line):
                        state = 4
                    else:
                        state = 0
            elif state == 3:
                m = re.search(r'\s*(?P<title>\S+.*\S+)\s*', line)
                if m:
                    title = m.group("title")
                    title = re.sub(r'^\s+|\s+$', '', title)
                    title = re.sub(r'&#39;', '\'', title)
                    title = re.sub(r'&#40;', ')', title)
                    title = re.sub(r'&#41;', '(', title)
                    title = re.sub(r'&lt;', '<', title)
                    title = re.sub(r'&gt;', '>', title)
                    title = re.sub(r'&nbsp;', ' ', title)
                    title = re.sub(r'&quot;', '"', title)
                    title = re.sub(r'</h3>', '', title)
                    if link and title:
                        result_list.append((link, title))
                    state = 0
            elif state == 4:
                m = re.search(r'(<i class="[^"]+" aria-label="[^"]+"></i>)?(?P<title>.*)</strong>', line)
                if m:
                    title = m.group("title")
                    title = re.sub(r'^\s+|\s+$', '', title)
                    title = re.sub(r'&#39;', '\'', title)
                    title = re.sub(r'&#40;', ')', title)
                    title = re.sub(r'&#41;', '(', title)
                    title = re.sub(r'&lt;', '<', title)
                    title = re.sub(r'&gt;', '>', title)
                    title = re.sub(r'&nbsp;', ' ', title)
                    title = re.sub(r'&quot;', '"', title)
                    title = re.sub(r'</h3>', '', title)
                    if link and title:
                        result_list.append((link, title))
                    state = 0
                else:
                    line = re.sub(r'<i class="[^"]+" aria-label="[^"]+"></i>', '', line)
                    title += line

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
	sys.exit(main())
