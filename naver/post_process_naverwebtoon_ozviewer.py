#!/usr/bin/env python3


import sys
import os
import re
import subprocess
from feedmakerutil import die, err, warn
from feedmakerutil import IO


def main():
    pageUrl = sys.argv[1]
    urlPrefix = ""
    dataUrl = ""

    for line in IO.read_stdin_as_line_list():
        m = re.search(r"jpg: '(?P<urlPrefix>[^']+\/){=filename}\?type=[^']+'", line)
        if m:
            urlPrefix = m.group("urlPrefix")
        else:
            m = re.search(r"documentURL:\s*'(?P<dataUrl>[^']+)'", line)
            if m:
                dataUrl = m.group("dataUrl")
                break
      
    if not dataUrl or urlPrefix:
        die("can't get a data url from input")
    
    cmd = "wget.sh '%s' utf8 | gunzip 2> /dev/null || wget.sh '%s' utf8" % (dataUrl, dataUrl)
    #print(cmd);
    with subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE) as p:
        for line in p.stdout:
            line = line.rstrip()
            matches = re.findall(r"[^\"]+\"\s*:\s*\"(assets/still/[^\"]+\.(?:png|jpg))\"", line)
            for match in matches:
                imgUrl = urlPrefix + match[0]
                print("<img src='%s' width='100%'/>" % (imgUrl))

                     
if __name__ == "__main__":
    sys.exit(main())
