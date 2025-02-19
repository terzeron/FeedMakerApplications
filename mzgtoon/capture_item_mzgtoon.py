#!/usr/bin/env python


import sys
import getopt
import json
from bin.feed_maker_util import IO, Config, URL


class InsufficientConfigError(Exception):
    def __init__(self, message):
        super().__init__(message)


def get_url_prefix_from_config():
    config = Config()
    conf = config.get_collection_configs()
    url_list = conf.get("list_url_list", [])
    if url_list:
        url = url_list[0]
        return URL.get_url_scheme(url) + "://" + URL.get_url_domain(url) + "/webtoon"
    raise InsufficientConfigError("Can't get url prefix from configuration")


def main():
    link = ""
    title = ""

    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    url_prefix = get_url_prefix_from_config()
            
    content = IO.read_stdin()
    data = json.loads(content)
    result_list = []
    item_list = data.get("listData", [])
    if item_list:
        for item in item_list:
            #no = item.get("list_no", 0)
            item_id = item.get("list_id", 0)
            episode = item.get("list_episode", 0)
            title = item.get("list_title", "")
            #update_time = item.get("list_update", "")
            #confirm = item.get("list_confirm", False)

            link = f"{url_prefix}/{item_id}/{episode}"
            result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
