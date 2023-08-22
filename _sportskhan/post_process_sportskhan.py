#!/usr/bin/env python


import sys
import re
from bin.feed_maker_util import IO


def main():
    urlList = []
    encoding = "cp949"

    for line in IO.read_stdin_as_line_list():
        line = line.rstrip()
        m = re.search(r"<a href='(?P<url>http://[^']+)'[^>]*>\d+</a>", line)
        if m:
            urlList.append(m.group("url"))
        else:
            m = re.search(r"<img src='(?P<url>[^']+)'[^>]*>", line)
            if m:
                print("<img src='%s' width='100%%'/>" % (m.group("url")))

    for url in urlList:
        cmd = "wget.sh '%s' %s" % (url, encoding)
        (result, error) = feed_maker_util.exec_cmd(cmd)
        if not error:
            for line in result.split("\n"):
                m = re.search(r"<img\s*[^>]*src=(?:'|\")?(?P<url>http://images.sportskhan.net/article/[^'\"\s]+)(?:'|\")?[^>]*>", line)
                if m:
                    print("<img src='%s' width='100%%'/>" % (m.group("url")))
                                        

if __name__ == "__main__":
    sys.exit(main())
