#!/usr/bin/env python


import sys
import re
from bin.feed_maker_util import IO


def main():
    secondPageUrl = ""

    for line in IO.read_stdin_as_line_list():
        line = line.rstrip()
        m = re.search(r"<a href='(?P<secondPageUrl>http://[^']+)'[^>]*><img src='http://cwstatic\.asiae\.co\.kr/images/cartoon/btn_s\.gif'/>", line)
        if m:
            secondPageUrl = m.group("secondPageUrl")
        else:
            m = re.search(r"<a href='(?P<secondPageUrl>http://stoo.asiae.co.kr/cartoon/view.htm[^']*)'>2페이지</a>", line)
            if m:
                secondPageUrl = m.group("secondPageUrl")
            else:
                m = re.search(r"<img src='(?P<imgUrl>http://cwcontent[^']+)'.*/>", line)
                if m:
                    imgUrl = m.group("imgUrl")
                    print("<img src='%s' width='100%%'/>" % (imgUrl))
            
    if secondPageUrl != "":
        cmd = "wget.sh '%s' | extract_element.py extraction" % (secondPageUrl)
        #print(cmd)
        (result, error) = feed_maker_util.exec_cmd(cmd)
        if not error:
            for line in result.split("\n"):
                m = re.search(r'<img\s*[^>]*src=(?:\'|\")(?P<imgUrl>http://cwcontent[^\'\"]+)(?:\'|\").*/>', line)
                if m:
                    imgUrl = m.group("imgUrl")
                    print("<img src='%s' width='100%%'/>" % (imgUrl))
                                        

if __name__ == "__main__":
    sys.exit(main())
