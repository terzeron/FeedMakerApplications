#!/usr/bin/env python


import sys
import os
import filecmp
from feed_maker_util import exec_cmd


def test_script(feed, script, work_dir, test_dir, index):
    os.chdir(work_dir)
    cmd = "cat %s/input.%d.txt | %s > %s/result.%d.temp" % (test_dir, index, script, test_dir, index)
    #print(cmd)
    (result, error) = exec_cmd(cmd)
    if not error:
        os.chdir(test_dir)
        return filecmp.cmp("result.%d.temp" % (index), "expected.output.%d.txt" % (index)), "", cmd
    print(error)
    return False, error, cmd


def main():
    fm_cwd = os.getenv("FEED_MAKER_WORK_DIR")

    test_subjects = {
        "java/javabeat": [ "./capture_item_link_title.py" ],
        "naver/navercast": [ "../capture_item_navercast.py" ],
        "naver/naverblog.pjwwoo": [ "../capture_item_naverblog.py" ],
        "naver/dice": [ "../capture_item_naverwebtoon.py" ],
        "naver/naverwebtoon": [ "./capture_item_link_title.py" ],
        "naver/naverpost.businessinsight": [ "../capture_item_naverpost.py", "../post_process_naverpost.py" ],
        "myktoon/myktoon": [ "./capture_item_link_title.py" ],
        "myktoon/god_of_poverty": [ "../capture_item_myktoon.py", "../post_process_myktoon.py 'https://v2.myktoon.com/web/works/viewer.kt?timesseq=141841'" ],
        "egloos/oblivion": [ "../capture_item_link_title.py" ],
        "daum/redstorm": [ "../capture_item_daumwebtoon.py", "../post_process_daumwebtoon.py 'http://cartoon.media.daum.net/m/webtoon/viewer/46901'" ],
        "daum/daumwebtoon": [ "./capture_item_link_title.py" ],
        "khan/hammer": [ "./capture_item_link_title.py" ],
        "tistory/nasica1": [ "../capture_item_tistory.py" ],
        "kakao/revivalofstudent": [ "../capture_item_kakaowebtoon.py" ],
        "kakao/kakaowebtoon": [ "./capture_item_link_title.py" ],
    }
    
    for (feed, scripts) in test_subjects.items():
        index = 0
        for script in scripts:
            index += 1
            print(feed, index, script)
            work_dir = fm_cwd + "/" + feed
            test_dir = fm_cwd + "/test/" + feed
            result, error, cmd = test_script(feed, script, work_dir, test_dir, index)
            if error:
                print("Error in %s of %s\n%s\n%s" % (feed, script, cmd, error))
                return -1
    print("Ok")
    
                
if __name__ == "__main__":
   sys.exit(main())
