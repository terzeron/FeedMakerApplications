#!/usr/bin/env python


import sys
import re
import getopt
from typing import List, Tuple

from bin.feed_maker_util import IO
from bin.crawler import Crawler
from utils.translation import Translation


def main() -> int:
    num_of_recent_feeds = 1000
    debug = False

    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:d")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)
        elif o == '-d':
            debug = True

    line_list = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str, str]] = []
    issue_links_set = set()
    crawler = Crawler(render_js=False, timeout=60)

    current_link = None
    for line in line_list:
        # communication_archive.html:
        # <a class="archive-issue-timeline-issues-item" href="https://cacm.acm.org/issue/january-2026/">
        # <span class="archive-issue-timeline-issues-item-title">
        # January 2026
        m = re.search(r'<a class="archive-issue-timeline-issues-item" href="([^"]+)">', line)
        if m:
            current_link = m.group(1)
            continue

        if current_link:
            # title이 있는 줄 찾기 (</span> 태그 포함 가능)
            title_match = re.search(r'^\s*([A-Za-z]+\s+\d{4})\s*(?:</span>)?', line)
            if title_match:
                issue_link = current_link
                if issue_link not in issue_links_set:
                    issue_links_set.add(issue_link)

                    html, error, _ = crawler.run(issue_link)

                    if debug and html:
                        issue_name = issue_link.rstrip('/').split('/')[-1]
                        with open(f"debug_cacm_{issue_name}.html", "w") as f:
                            f.write(html)

                    if html and not error:
                        # article 링크 추출: <a href="https://cacm.acm.org/(opinion|news|practice|research)/xxx/">Title</a>
                        matches = re.findall(
                            r'<a href="(https://cacm\.acm\.org/(?:opinion|news|practice|research|blogcacm)/[^"]+/)">([^<]+)</a>',
                            html
                        )
                        seen_links = set()
                        for match in matches:
                            link = match[0]
                            title = match[1].strip()
                            if title and link not in seen_links:
                                seen_links.add(link)
                                result_list.append((link, title))
                current_link = None

    translation = Translation()
    result_list = translation.translate(result_list[:num_of_recent_feeds])

    for (link, title) in result_list[:num_of_recent_feeds]:
        print(f"{link}\t{title}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
