#!/usr/bin/env python3

import sys
import re
import json
import feedmakerutil


def main():
    state = 0
    
    lineList = feedmakerutil.read_stdin_as_line_list()
    for line in lineList:
        #print(line)
        if state == 0:
            if re.search(r'<script[^>]*id="__clipContent">', line):
                state = 1
        elif state == 1:
            if re.search(r'</script>', line):
                state = 0
            else:
                print(line)
                    
        
if __name__ == "__main__":
    sys.exit(main())

    
