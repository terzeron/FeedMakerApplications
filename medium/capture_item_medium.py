#!/usr/bin/env python


import sys
import re
import getopt
import json
from bin.feed_maker_util import IO, URL


def main():
    link = ""
    title = ""
    state = 0

    num_of_recent_feeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<link rel="canonical" href="(?P<page_url>[^"]+)">', line)
            if m:
                page_url = m.group("page_url")
                state = 1
        elif state == 1:
            m = re.search(r'^window\["obvInit"\]\((?P<json>.*)\)$', line)
            if m:
                json_content = m.group("json")
                json_content = json_content.replace(r'\x3c', '<')
                json_content = json_content.replace(r'\x3e', '>')
                json_data = json.loads(json_content)
                if json_data:
                    if "references" in json_data:
                        if "Post" in json_data["references"]:
                            for item in json_data["references"]["Post"]:
                                item_data = json_data["references"]["Post"][item]
                                if "title" in item_data and "uniqueSlug" in item_data:
                                    if "content" in item_data and "subtitle" in item_data["content"]:
                                        main_title = re.sub(r'\n', ' ', item_data["title"])
                                        sub_title = re.sub(r'\n', ' ', item_data["content"]["subtitle"])
                                        title = main_title + " " + sub_title
                                        link = page_url + "/" + item_data["uniqueSlug"]
                                        result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
