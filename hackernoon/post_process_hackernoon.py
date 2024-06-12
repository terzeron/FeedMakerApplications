#!/usr/bin/env python


import sys
import re
import json
from bin.feed_maker_util import IO, header_str


def main():
    print(header_str)
    
    matches = re.findall(r'<script[^>]*>(?P<json_str>{.+?})</script>', IO.read_stdin())
    for match in matches:
        data = json.loads(match)
        if "props" in data:
            props = data["props"]
            if "pageProps" in props:
                page_props = props["pageProps"]
                if "data" in page_props:
                    d = page_props["data"]
                    if "parsed" in d:
                        parsed = d["parsed"]
                        print(parsed)
                    elif "articleBody" in d:
                        article_body = d["articleBody"]
                        article_body = re.sub(r"\. ", ".<br>\n", article_body)
                        print(article_body)
                        

if __name__ == "__main__":
    sys.exit(main())
