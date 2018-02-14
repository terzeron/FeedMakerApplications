#!/usr/bin/env python


import sys
import os
import filecmp
import feedmakerutil


def test_script(feed, script, work_dir, test_dir, index):
    os.chdir(work_dir)
    cmd = "cat %s/input.%d.txt | %s > %s/result.%d.temp" % (test_dir, index, script, test_dir, index)
    #print(cmd)
    (result, error) = feedmakerutil.exec_cmd(cmd)
    if not error:
        os.chdir(test_dir)
        return filecmp.cmp("result.%d.temp" % (index), "expected.output.%d.txt" % (index))
    return False


def main():
    fm_cwd = os.getenv("FEED_MAKER_CWD")

    test_subjects = {
        "naver/dice": [ "../capture_item_naverwebtoon.py" ],
        "naver/naverblog.pjwwoo": [ "../capture_item_naverblog" ],
        "naver/navercast": [ "../capture_item_navercastpc.py" ],
        "naver/naverpost.businessinsight": [ "../capture_item_naverpost.py", "../post_process_naverpost.py" ],
        "naver/magazines": [ "./capture_item_link_title.py", "./post_process_magazines.py" ],
        "cine21/cine21.review": [ "../capture_item_cine21.py" ],
        "javabeat/javabeat": [ "./capture_item_link_title.py" ],
    }
    
    for (feed, scripts) in test_subjects.items():
        index = 0
        for script in scripts:
            index += 1
            print(feed, index, script)
            work_dir = fm_cwd + "/" + feed
            test_dir = fm_cwd + "/test/" + feed
            if not test_script(feed, script, work_dir, test_dir, index):
                print("Error in %s of %s" % (feed, script))

                
if __name__ == "__main__":
   sys.exit(main())
