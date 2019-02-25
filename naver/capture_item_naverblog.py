#!/usr/bin/env python


import sys
import re
import getopt
import urllib.parse
from feed_maker_util import IO


def main():
    link = ""
    title = ""
    urlPrefix = "http://blog.naver.com/PostView.nhn?blogId="

    numOfRecentFeeds = 30
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    resultList = []
    for line in IO.read_stdin_as_line_list():
        m = re.search(r'"blogId"\s*:\s*"(?P<blogId>[^"]+)"', line)
        if m:
            urlPrefix = urlPrefix + m.group("blogId") + "&logNo="
        matches = re.findall(r'"logNo":"(\d+)","title":"([^"]+)",', line)
        for match in matches:
            logNo = match[0]
            title = urllib.parse.unquote(match[1])
            title = re.sub(r"\+", " ", title)
            title = re.sub(r"&quot;", "'", title)
            title = re.sub(r"&(lt|gt);", "", title)
            title = re.sub(r"\n", " ", title)
            resultList.append((logNo, title))


    for (logNo, title) in resultList[:numOfRecentFeeds]:
        link = urlPrefix + logNo
        print("%s\t%s" % (link, title))
        
            

if __name__ == "__main__":
    sys.exit(main())
