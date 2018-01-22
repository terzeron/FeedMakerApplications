#!/usr/bin/env python


import sys
import re
import urllib.parse
import feedmakerutil


def main():
    link = ""
    title = ""
    urlPrefix = "http://blog.naver.com/PostView.nhn?blogId="

    resultList = []
    for line in feedmakerutil.read_stdin_as_line_list():
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
            resultList.append((logNo, title))


    for (logNo, title) in resultList:
        link = urlPrefix + logNo
        print("%s\t%s" % (link, title))
        
            

if __name__ == "__main__":
    sys.exit(main())
