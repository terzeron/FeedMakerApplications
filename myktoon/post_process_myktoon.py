#!/usr/bin/env python3

import io
import os
import sys
import re
import getopt
from urllib.parse import urlparse, parse_qs
import requests
import feed_maker_util


def main():
    # url parsing
    url = sys.argv[1]
    parsedUrl = urlparse(url)
    parsedParams = parse_qs(parsedUrl.query)
    timesseq = parsedParams['timesseq'][0]
    dataUrl = "https://v2.myktoon.com/web/works/times_image_list_ajax.kt?timesseq=" + timesseq

    headers = { "Referer": url }
    response = requests.get(dataUrl, headers=headers)
    
    # read data from reponse
    #print(response.json())
    for item in response.json()['response']:
        #print(item)
        if item['imagepath']:
            print("<img src='%s' width='100%%'>" % item['imagepath'])

        
if __name__ == "__main__":
    sys.exit(main())
