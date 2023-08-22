#!/usr/bin/env python


import sys
import re
import getopt
import json
from bs4 import BeautifulSoup
from bin.feed_maker_util import IO

    
def main():
    link = ""
    title = ""

    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    result_list = []
    #html_str = IO.read_stdin()
    #soup = BeautifulSoup(html_str, "html.parser")
    #json_data = soup.pre.text
    #data = json.loads(json_data)
    data = json.loads(IO.read_stdin())
    if data:
        for item in data:
            if "subject" in item and "permanentLink" in item:
                link = item["permanentLink"]
                title = item["subject"]
                result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))
                
            
if __name__ == "__main__":
    sys.exit(main())
