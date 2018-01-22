#!/usr/bin/env python3


import io
import os
import sys
import re
import feedmakerutil


def getUrlDomainFromConfig():
    config = feedmakerutil.read_config()
    collection = feedmakerutil.get_config_node(config, "collection")
    listUrlList = feedmakerutil.get_config_node(collection, "list_url_list")
    listUrl = feedmakerutil.get_config_node(listUrlList, "list_url")
    url = feedmakerutil.get_value_from_config(listUrl)
    return feedmakerutil.get_url_domain(url)
    
    
def main():
    urlDomain = getUrlDomainFromConfig();
    
    lineList = feedmakerutil.read_stdin_as_line_list()
    for line in lineList:
        matches = re.findall(r'<a href="/(\d+)"[^>]*>([^<]*)</a>', line)

        for match in matches:
            link = urlDomain + match[0]
            title = match[1]
            print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    main()
        
