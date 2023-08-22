#!/usr/bin/env python


import sys
import re
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    linkPrefix = "http://comic.mt.co.kr/"

    for line in IO.read_stdin_as_line_list():
        m = re.search(r'''
        <li>
        <a\s+href="\./(?P<link>comicView\.htm[^"]+)">
        <img\s+height="\d+"\s+src="[^"]+"\s+width="\d+"\s*/>
        </a>
        <p\ class="[^"]+">
        (?P<title1>[^<]+)
        <br/?>
        <b>
        (?P<title2>[^<]*)
        </b>
        (?:</br>)?
        </p>
        </li>
        ''', line, re.VERBOSE)
        if m:
            link = linkPrefix + m.group("link")
            title = m.group("title1") + " " + m.group("title2")
            link = re.sub(r"&amp;", "&", link)
            link = re.sub(r"&nPage=[^&]*", "", link)
            print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    sys.exit(main())
