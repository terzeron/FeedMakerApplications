#!/usr/bin/env python


import os
import sys
import re
import json
import getopt
import requests
import logging
import logging.config
from feedmakerutil import IO, Config


logging.config.fileConfig(os.environ["FEED_MAKER_HOME_DIR"] + "/bin/logging.conf")
logger = logging.getLogger()


def get_page_content(url, encoding, data, header = {}):
    #print(data, header)
    response = requests.post(url, data = data, headers = header)
    return response.text


def main():
    url_prefix = "https://page.kakao.com/viewer?productId="
    
    num_of_recent_feeds = 20
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    series_id = None
    for line in IO.read_stdin_as_line_list():
        m = re.search(r'"seriesId"\s*:\s*(?P<series_id>\d+)', line)
        if m:
            series_id = m.group("series_id")
    if not series_id:
        logger.error("can't find series id from HTML")
        return -1
        
    api_url = "https://api2-page.kakao.com/api/v5/store/singles"
    data = {"seriesid": series_id, "page": 0, "direction": "desc", "page_size": num_of_recent_feeds, "without_hidden": "true"}
    config = Config()
    collection_conf = config.get_collection_configs()
    page_content = get_page_content(api_url, collection_conf["encoding"], data)
    response = json.loads(page_content)
    #pprint.pprint(response)

    result_list = []
    if "singles" in response:
        for s in response["singles"]:
            #pprint.pprint(s)
            link = url_prefix + str(s["id"])
            title = s["title"]
            result_list.append((link, title))

    for link, title in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
