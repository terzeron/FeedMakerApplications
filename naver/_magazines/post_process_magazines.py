#!/usr/bin/env python


import sys
import re
from bin.feed_maker_util import IO


def main():
    state = 0
    for line in IO.read_stdin_as_line_list():
        line = line.rstrip()
        if state == 0:
            pat = r'<img src=\"http://imgnews.naver.(com|net)/image/sports/\d+/magazineS/magazine_content/magazineS_\d+/\d+_file_image_0.jpg\" width=\"67\" height=\"9\" alt=\"[^\"]+\" />'
            m = re.search(pat, line)
            if m:
                line = re.sub(pat, 'PEOPLE', line)
                state = 1
        elif state == 1:
            pat = r'<img src=\"http://imgnews.naver.(com|net)/image/sports/\d+/magazineS/magazine_content/magazineS_\d+/\d+_file_image_0.jpg\" width=\"102\" height=\"10\" alt=\"[^\"]+\" />'
            m = re.search(pat, line)
            if m:
                line = re.sub(pat, 'SPECIAL REPORT', line)
                state = 2
        elif state == 2:
            pat = r'<img src=\"http://imgnews.naver.(com|net)/image/sports/\d+/magazineS/magazine_content/magazineS_\d+/\d+_file_image_0.jpg\" width=\"57\" height=\"10\" alt=\"[^\"]+\" />'
            m = re.search(pat, line)
            if m:
                line = re.sub(pat, 'COLUMN', line)
                state = 3
        elif state == 3:
            pat = r'<h2><img src=\"http://imgnews.naver.(com|net)/image/sports/\d+/magazineS/magazine_content/magazineS_\d+/\d+_file_image_0.jpg\" width=\"58\" height=\"10\" alt=\"[^\"]+\" /></h2>.*'
            m = re.search(pat, line)
            if m:
                line = re.sub(pat, '', line)
                state = 4
        elif state == 4:
            pat = r'<img src=\"http://imgnews.naver.(com|net)/image/sports/\d+/magazineS/magazine_content/magazineS_\d+/\d+_file_image_0.jpg\" width=\"29\" height=\"10\" alt=\"[^\"]+\" />'
            m = re.search(pat, line)
            if m:
                line = re.sub(pat, 'POLL', line)
                state = 5
            else:
                continue
        elif state == 5:
            pat = r'^<div><ul>'
            m = re.search(pat, line)
            if m:
                line = re.sub(pat, '<h2>ZOOM IN</h2><ul>', line)
                state = 6
        elif state == 6:
            pat = r'^</li></ul></div>'
            m = re.search(pat, line)
            if m:
                line = re.sub(pat, '</li></ul>', line)
                break
        print(line)
        

if __name__ == "__main__":
    sys.exit(main())
