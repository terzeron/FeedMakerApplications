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
        "naver/navercast": [ "../capture_item_navercast.py" ],
        "naver/naverblog.pjwwoo": [ "../capture_item_naverblog.py" ],
        "naver/private_educational_institute_in_end_of_a_century": [ "../capture_item_naverwebtoon.py" ],
        "naver/naverwebtoon": [ "./capture_item_link_title.py" ],
        "naver/naverpost.businessinsight": [ "../capture_item_naverpost.py", "../post_process_naverpost.py" ],
        "kakao/monk_xuanzang": [ "../capture_item_kakaowebtoon.py" ],
        "kakao/kakaowebtoon": [ "./capture_item_link_title.py" ],
        "daum/matchless_abi": [ "../capture_item_daumwebtoon.py", "../post_process_daumwebtoon.py 'http://cartoon.media.daum.net/m/webtoon/viewer/45820'" ],
        "daum/daumwebtoon": [ "./capture_item_link_title.py" ],
        "tistory/nasica1": [ "../capture_item_tistory.py" ],
        "egloos/oblivion": [ "../capture_item_link_title.py" ],
        #"study/javabeat": [ "./capture_item_link_title.py" ],
        "manatoki/level_up_alone" : [ "../capture_item_manatoki.py" ],
        "jmana/one_punch_man_remake" : [ "../capture_item_jmana.py" ],
        "wfwf/warrior_at_fff_level" : [ "../capture_item_wfwf.py" ],
        "wtwt/login_alone" : [ "../capture_item_wtwt.py" ],
        "marumaru/ride_on_king" : [ "../capture_item_marumaru.py" ],
    }
    
    for (feed, scripts) in test_subjects.items():
        index = 0
        for script in scripts:
            index += 1
            print(feed)
            work_dir = fm_cwd + "/" + feed
            test_dir = fm_cwd + "/test/" + feed
            result, error, cmd = test_script(feed, script, work_dir, test_dir, index)
            if error:
                print("Error in %s of %s\n%s\n%s" % (feed, script, cmd, error))
                return -1
    print("Ok")
    
                
if __name__ == "__main__":
   sys.exit(main())
