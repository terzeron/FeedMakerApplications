#!/usr/bin/env python

import sys
import re
import json
from bin.feed_maker_util import IO


def main():
    clipNoList = []
    volumeNo = None
    memberNo = None

    m = re.search(r'volumeNo=(?P<volumeNo>\d+)&memberNo=(?P<memberNo>\d+)', sys.argv[1])
    if m:
        volumeNo = int(m.group("volumeNo"))
        memberNo = int(m.group("memberNo"))

    lineList = IO.read_stdin_as_line_list()
    for line in lineList:
        line = line.rstrip()
        line = re.sub(r'[\x01\x08]', '', line, re.LOCALE)
        print(line)

    failureCount = 0
    link_prefix = "http://m.post.naver.com/viewer/clipContentJson.naver?volumeNo=%d&memberNo=%d&clipNo=" % (volumeNo, memberNo)
    for clipNo in range(30):
        link = link_prefix + str(clipNo)
        cmd = 'wget.sh "%s" utf8' % (link)
        #print(cmd)
        (result, error) = feed_maker_util.exec_cmd(cmd)
        if error or re.search(r'"notExistClip"', result):
            failureCount = failureCount + 1
            if failureCount > 2:
                break
        else:
            clipContent = json.loads(result)["clipContent"]
            clipContent = re.sub(r'src="{{{[^\|]*\|/([^\|]+)\|\d+|\d+}}}"', r'src="http://post.phinf.naver.net/\1"', clipContent)
            clipContent = re.sub(r'<img src=\'http://static.post.naver.net/image/im/end/toast_flick.png\'/>', '', clipContent)
            #clipContent = re.sub(r'[\x01\x08]', '', clipContent, re.LOCALE)
            print(clipContent)
        
if __name__ == "__main__":
    sys.exit(main())

    
