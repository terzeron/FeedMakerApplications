#!/usr/bin/env python3


import io
import os
import sys
import re
import feedmakerutil


def getUrlDomainFromConfig():
    config = feedmakerutil.readConfig()
    collection = feedmakerutil.getConfigNode(config, "collection")
    listUrlList = feedmakerutil.getConfigNode(collection, "list_url_list")
    listUrl = feedmakerutil.getConfigNode(listUrlList, "list_url")
    url = feedmakerutil.getValueFromConfig(listUrl)
    return feedmakerutil.getUrlDomain(url)
    
    
def main():
    urlDomain = getUrlDomainFromConfig();
    
    lineList = feedmakerutil.readStdinAsLineList()
    for line in lineList:
        matches = re.findall(r'<a href="/(\d+)"[^>]*>([^<]*)</a>', line)

        for match in matches:
            link = urlDomain + match[0]
            title = match[1]
            print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    main()
        
