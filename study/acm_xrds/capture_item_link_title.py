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

    for line in line_list:
        # xrds_archive.html: <h3><a href="archives.cfm?iid=3764099">Summer 2025 | Volume 31, No. 4</a></h3>
        m = re.search(r'<h3><a href="(archives\.cfm\?iid=\d+)">', line)
        if m:
            issue_link = "https://xrds.acm.org/" + m.group(1)
            if issue_link not in issue_links_set:
                issue_links_set.add(issue_link)
                print(f"Crawling {issue_link}...", file=sys.stderr)

                html, error, _ = crawler.run(issue_link)

                if debug and html:
                    iid = m.group(1).split('=')[1]
                    with open(f"debug_xrds_{iid}.html", "w") as f:
                        f.write(html)
                    print(f"  Saved to debug_xrds_{iid}.html", file=sys.stderr)

                if html and not error:
                    # article 링크 추출: <h3><a href="article.cfm?aid=XXXXXX">Title</a></h3>
                    matches = re.findall(r'<h3><a href="(article\.cfm\?aid=\d+)">([^<]+)</a></h3>', html)
                    for match in matches:
                        link = "https://xrds.acm.org/" + match[0]
                        title = match[1].strip()
                        if title and (link, title) not in result_list:
                            result_list.append((link, title))
                    print(f"  Found {len(matches)} articles", file=sys.stderr)
                else:
                    print(f"  Error: {error}", file=sys.stderr)

    translation = Translation()
    result_list = translation.translate(result_list[:num_of_recent_feeds])

    for (link, title) in result_list[:num_of_recent_feeds]:
        print(f"{link}\t{title}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
