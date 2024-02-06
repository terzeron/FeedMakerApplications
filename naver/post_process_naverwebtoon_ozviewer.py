#!/usr/bin/env python


import sys
import os
import re
import subprocess
import logging
import logging.config
from bin.feed_maker_util import IO


logging.config.fileConfig(os.environ["FM_HOME_DIR"] + "/logging.conf")
logger = logging.getLogger()


def main():
    page_url = sys.argv[1]
    url_prefix = ""
    data_url = ""

    for line in IO.read_stdin_as_line_list():
        m = re.search(r"jpg: '(?P<url_prefix>[^']+\/){=filename}\?type=[^']+'", line)
        if m:
            url_prefix = m.group("url_prefix")
        else:
            m = re.search(r"documentURL:\s*'(?P<data_url>[^']+)'", line)
            if m:
                data_url = m.group("data_url")
                break
      
    if not data_url or url_prefix:
        logger.error("can't get a data url from input")
        return -1
    
    cmd = "wget.sh '%s' utf8 | gunzip 2> /dev/null || wget.sh '%s' utf8" % (data_url, data_url)
    #print(cmd);
    with subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE) as p:
        for line in p.stdout:
            line = line.rstrip()
            matches = re.findall(r"[^\"]+\"\s*:\s*\"(assets/still/[^\"]+\.(?:png|jpg))\"", line)
            for match in matches:
                img_url = url_prefix + match[0]
                print("<img src='%s' width='100%'/>" % (img_url))

                     
if __name__ == "__main__":
    sys.exit(main())
