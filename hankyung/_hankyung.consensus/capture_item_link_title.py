#!/usr/bin/env python


import sys
import re
import getopt
import json
from feed_maker_util import IO


def main():
    link = ""
    title = ""

    num_of_recent_feeds = 3000
    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    result_list = []
    data = IO.read_stdin()
    json_data = json.loads(data)
    if json_data:
        if "data" in json_data:
            data = json_data["data"]
            for _, v in data.items():
                #import pprint
                #pprint.pprint(v)
                if "REPORT_TITLE" in v and "REPORT_FILEPATH" in v:
                    title = v["REPORT_TITLE"]
                    if re.search(r'^\S+\(\d+\)\s+', title):
                        continue
                    if re.search(r'(주간|week(ly)?|월간?|month(ly)?|연간|년|year(ly)?)', title, re.IGNORECASE):
                        link = v["REPORT_FILEPATH"]
                        result_list.append((link, title))

    result_list = sorted(result_list, key = lambda x: x[1])
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
