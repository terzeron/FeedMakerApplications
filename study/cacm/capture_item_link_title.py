#!/usr/bin/env python


import sys
import re
import getopt
from typing import List, Tuple

from bin.feed_maker_util import IO
from bin.crawler import Crawler
from utils.translation import Translation


def main() -> int:
    state = 0
    num_of_recent_feeds = 1000
    
    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)
            
    line_list = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str, str]] = []
    crawler = Crawler(render_js=False)
    for line in line_list:
        if state == 0:
            m = re.search(r'<a class="archive-issue-timeline-issues-item" href="(?P<issue_link>https://cacm.acm.org/issue/[^"]+)">', line)
            if m:
                issue_link = m.group("issue_link")
                html, error, _ = crawler.run(issue_link)
                if html and not error:
                    matches = re.findall(r'<a href="(https://cacm.acm.org/(\w+)/[^"]+)">([^<]+)</a>', html)
                    for match in matches:
                        if match[1] not in ("section", "category", "account"):
                            link = match[0]
                            title = match[2]
                            result_list.append((link, title))

    result_list = Translation.translate(result_list[:num_of_recent_feeds])
                            
    for (link, title) in result_list[:num_of_recent_feeds]:
        print(f"{link}\t{title}")

    return 0
        

if __name__ == "__main__":
    sys.exit(main())
