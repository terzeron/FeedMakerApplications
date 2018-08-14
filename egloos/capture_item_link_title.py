#!/usr/bin/env python3


import io
import os
import sys
import re
import getopt
from feedmakerutil import Config, IO, URL


def get_url_from_config():
    config = Config()
    collection = config.get_collection_configs()
    url = collection["list_url_list"][0]
    return url
    
    
def main():
    url = get_url_from_config()

    num_of_recent_feeds = 1000
    count = 0
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)
    
    line_list = IO.read_stdin_as_line_list()
    result_list = []
    state = 0
    for line in line_list:
        if state == 0:
            m = re.search(r'<strong class="title">', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(r'<a href="(?P<article_id>/\d+)"[^>]*title="(?P<title>[^"]+)"[^>]*>', line)
            if m:
                link = url + m.group("article_id")
                title = m.group("title")
                result_list.append((link, title))
                state = 2
        elif state == 2:
            m = re.search(r'</strong>', line)
            if m:
                state = 0

    for (link, title) in result_list[-num_of_recent_feeds:]:
        print("%s\t%s" % (link, title))
                
            
if __name__ == "__main__":
    main()
        
