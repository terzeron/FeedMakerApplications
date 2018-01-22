#!/usr/bin/env python3


import sys
import re
import http.client
import feedmakerutil


def main():
    imgHost = ""
    imgPath = ""
    imgIndex = -1
    imgExt = "jpg"
    pageUrl = sys.argv[1]

    for line in feedmakerutil.read_stdin_as_line_list():
        line = line.rstrip()
        if re.search(r"<(meta|style)", line):
            print(line)
        else:
            m = re.search(r"<img src='http://(?P<imgHost>imgcomic.naver.(?:com|net))/(?P<imgPath>[^']+_)(?P<imgIndex>\d+)\.(?P<imgExt>jpg|gif)", line, re.IGNORECASE)
            if m:
                imgHost = m.group("imgHost")
                imgPath = m.group("imgPath")
                imgIndex = int(m.group("imgIndex"))
                imgExt = m.group("imgExt")
                print("<img src='http://%s/%s%d.%s' width='100%%'/>" % (imgHost, imgPath, imgIndex, imgExt))
            else:
                m = re.search(r"<img src='http://(?P<imgHost>imgcomic.naver.(?:com|net))/(?P<imgPath>[^']+)\.(?P<imgExt>jpg|gif)", line, re.IGNORECASE)
                if m:
                    imgHost = m.group("imgHost")
                    imgPath = m.group("imgPath")
                    imgExt = m.group("imgExt")
                    print("<img src='http://%s/%s.%s' width='100%%'/>" % (imgHost, imgPath, imgExt))
        
    if imgPath != "" and imgIndex >= 0:
        # add some additional images loaded dynamically
        for i in range(60):
            imgUrl = "http://%s/%s%d.%s" % (imgHost, imgPath, i, imgExt)
            cmd = 'wget.sh --spider --referer "%s" "%s"' % (pageUrl, imgUrl)
            result = feedmakerutil.exec_cmd(cmd)
            if result:
                print("<img src='http://%s/%s%d.%s' width='100%%'/>" % (imgHost, imgPath, i, imgExt))
        
    
    


if __name__ == "__main__":
    sys.exit(main())
