#!/usr/bin/env python


import sys
import re
import getopt
import urllib.parse
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    url_prefix = "http://blog.naver.com/PostView.naver?blogId="

    num_of_recent_feeds = 30
    optlist, _ = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    result_list = []
    for line in IO.read_stdin_as_line_list():
        m = re.search(r'"blogId"\s*:\s*"(?P<blogId>[^"]+)"', line)
        if m:
            url_prefix = url_prefix + m.group("blogId") + "&logNo="

        matches = re.findall(r'"logNo":"(\d+)","title":"([^"]+)",', line)
        for match in matches:
            log_no = match[0]
            link = log_no
            title = urllib.parse.unquote(match[1])
            title = re.sub(r"\+", " ", title)
            title = re.sub(r"&quot;", "'", title)
            title = re.sub(r"&(lt|gt);", "", title)
            title = re.sub(r"\n", " ", title)
            result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (url_prefix + link, title))


if __name__ == "__main__":
    sys.exit(main())
