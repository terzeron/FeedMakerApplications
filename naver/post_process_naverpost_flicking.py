#!/usr/bin/env python3

import sys
import re
import json
import feedmakerutil


def main():
    clipNoList = []
    volumeNo = None
    memberNo = None

    m = re.search(r'volumeNo=(?P<volumeNo>\d+)&memberNo=(?P<memberNo>\d+)', sys.argv[1])
    if m:
        volumeNo = int(m.group("volumeNo"))
        memberNo = int(m.group("memberNo"))

    lineList = feedmakerutil.readStdinAsLineList()
    for line in lineList:
        line = line.rstrip()
        print(line)

    failureCount = 0
    link_prefix = "http://m.post.naver.com/viewer/clipContentJson.nhn?volumeNo=%d&memberNo=%d&clipNo=" % (volumeNo, memberNo)
    for clipNo in range(30):
        link = link_prefix + str(clipNo)
        cmd = 'wget.sh "%s" utf8' % (link)
        #print(cmd)
        result = feedmakerutil.execCmd(cmd)
        if result == False or re.search(r'"notExistClip"', result):
            failureCount = failureCount + 1
            if failureCount > 2:
                break
        else:
            print(json.loads(result)["clipContent"])
        
if __name__ == "__main__":
    sys.exit(main())

    
