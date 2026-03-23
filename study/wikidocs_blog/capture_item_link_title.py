#!/usr/bin/env python


import sys
import re
import getopt
from typing import List, Tuple

from bin.feed_maker_util import IO


def main() -> int:
    num_of_recent_feeds = 20

    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str, str]] = []
    seen_links = set()

    current_link = None
    in_h2 = False
    for line in line_list:
        # <a href="/blog/@username/9698/" class="block">
        m = re.search(r'<a\s+href="(/blog/@[^"]+/\d+/)"[^>]*class="block"', line)
        if m:
            current_link = "https://wikidocs.net" + m.group(1)
            in_h2 = False
            continue

        if current_link:
            # <h2 class="text-xl font-bold ...">
            if re.search(r'<h2[^>]*class="text-xl font-bold', line):
                in_h2 = True
                continue

            if in_h2:
                title = re.sub(r"<[^>]+>", "", line).strip()
                if not title:
                    continue
                if current_link not in seen_links:
                    seen_links.add(current_link)
                    result_list.append((current_link, title))
                current_link = None
                in_h2 = False

    for link, title in result_list[:num_of_recent_feeds]:
        print(f"{link}\t{title}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
