#!/usr/bin/env python3


import io
import os
import sys
import re
import getopt
from feedmakerutil import Config, IO, URL


def get_url_domain_from_config():
    config = Config.read_config()
    collection = Config.get_config_node(config, "collection")
    list_url_list = Config.get_config_node(collection, "list_url_list")
    list_url = Config.get_config_node(list_url_list, "list_url")
    url = Config.get_value_from_config(list_url)
    return URL.get_url_domain(url)
    
    
def main():
    url_domain = get_url_domain_from_config()
    state = 0

    num_of_recent_feeds = 1000
    count = 0
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)
    
    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        '''
        matches = re.findall(r'<a href="/(\d+)"[^>]*>([^<]*)</a>', line)
        for match in matches:
            link = url_domain + match[0]
            title = match[1]
            print("%s\t%s" % (link, title))
        '''
        if state == 0:
            m = re.search(r'<strong class="title">', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(r'^\s*(?P<title>.*)\s*$', line)
            if m:
                title = m.group("title")
                state = 2
        elif state == 2:
            m = re.search(r'<a class="post_link" href="(?P<url>[^"]+)"', line)
            if m:
                link = m.group("url")
                result_list.append((link, title))
                state = 0

    for (link, title) in result_list[-num_of_recent_feeds:]:
        print("%s\t%s" % (link, title))
                
            
if __name__ == "__main__":
    main()
        
