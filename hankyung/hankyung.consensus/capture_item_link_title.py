#!/usr/bin/env python


import sys
import re
import getopt
from feed_maker_util import IO


def main():
    link = ""
    url_prefix = "http://consensus.hankyung.com"
    title = ""
    state = 0

    num_of_recent_feeds = 3000
    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    result_list = []
    for line in IO.read_stdin_as_line_list():
        if state == 0:
            m = re.search(r'<td class="first txt_number">', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(r'<strong>\s*(?P<title>.+)\s*</strong>', line)
            if m:
                title = m.group("title")
                state = 2
        elif state == 2:
            m = re.search(r'<a href="(?P<link>[^"]+)"[^>]*><img src="/images/btn_attached.gif"', line)
            if m:
                link = url_prefix + m.group("link")
                if re.search(r'(주간|week(ly)?|월간?|month(ly)?|연간|년|year(ly)?)', title, re.IGNORECASE):
                    result_list.append((link, title))
                state = 0

    result_list = sorted(result_list, key = lambda x: x[1])
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
