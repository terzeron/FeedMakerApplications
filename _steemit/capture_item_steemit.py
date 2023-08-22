#!/usr/bin/env python


import sys
import re
import getopt
import urllib.parse
from typing import List, Tuple
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    url_prefix = "https://steemit.com"

    num_of_recent_feeds = 30
    optlist, _ = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    result_list: List[Tuple[str, str]] = []
    for line in IO.read_stdin_as_line_list():
        matches = re.findall(r'''
        <\w+
        \s+
        class="[^"]*entry-title[^"]*"
        [^>]*>
        \s*
        <a
        \s+
        href="(?P<link>[^"]+)"
        [^>]*>
        \s*
        (?:<!--[^>]*-->)?
        \s*
        (?P<title>\S.+?\S)
        \s*
        (?:<!--[^>]*-->)?
        \s*
        </a>
        ''', line, re.VERBOSE)
        for match in matches:
            link = url_prefix + match[0]
            title = urllib.parse.unquote(match[1])
            title = re.sub(r"\+", " ", title)
            title = re.sub(r"&quot;", "'", title)
            title = re.sub(r"&(lt|gt);", "", title)
            title = re.sub(r"\n", " ", title)
            result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
