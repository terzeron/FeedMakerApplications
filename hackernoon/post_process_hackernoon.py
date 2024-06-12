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
                    if "markup" in d and d["markup"]:
                        print(d["markup"])
                    elif "parsed" in d and d["parsed"]:
                        print(d["parsed"])
                        

if __name__ == "__main__":
    sys.exit(main())
