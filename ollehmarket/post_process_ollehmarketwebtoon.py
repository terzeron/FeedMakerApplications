#!/usr/bin/env python3

import io
import os
import sys
import re
import getopt
from urllib.parse import urlparse, parse_qs
import requests
import feedmakerutil


def main():
    # url parsing
    url = sys.argv[1]
    parsedUrl = urlparse(url)
    parsedParams = parse_qs(parsedUrl.query)
    webtoonseq = parsedParams['webtoonseq'][0]
    timesseq = parsedParams['timesseq'][0]
    dataUrl = "http://webtoon.olleh.com/api/work/getTimesDetailImageList.kt?mobileyn=N&webtoonseq=" + webtoonseq + "&timesseq=" + timesseq

    # request
    headers = { "Referer": url }
    response = requests.get(dataUrl, headers=headers)
    
    # read data from reponse
    for item in response.json()['imageList']:
        print("<img src='%s' width='100%%'>" % item['imagepath'])

        
if __name__ == "__main__":
    main()
