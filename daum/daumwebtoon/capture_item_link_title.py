#!/usr/bin/env python


import io
import os
import sys
import re
import json
from feed_maker_util import IO


def main():
    link_prefix = "http://cartoon.media.daum.net/webtoon/view/"

    json_str = IO.read_stdin()
    json_obj = json.loads(json_str)
    for item in json_obj["data"]:
        link = link_prefix + item["nickname"]
        title = item["title"]
        if re.search(r'(그녀|사랑|신랑|악녀|키스|곡|선녀|마녀|오빠|사귀|사귄|헤어지|헤어진|연애|썸|순정|열애|고백|왕비|후궁|공주|왕녀|황녀|황비|너|남녀|러브|질투)', title):
            continue
        if title in ("강호표사", "트레이스", "대선비쇼에 어서오세요!", "화폐개혁", "아비무쌍", "노력의 卍(만)", "쌍갑포차", "특별직", "어름치", "랑데부", "피치 (PITCH)", "남궁세가 소공자", "레드스톰", "여의주", "표류감옥", "나 홀로 버그로 꿀빠는 플레이어", "학교대표", "흑우", "고교호구왕", "논현동 장사꾼", "풍검", "블랙 베히모스", "교수님을 빚는 중", "봄날의 팔광"):
            continue
        if item["ageGrade"] == 0:
            print("%s\t%s" % (link, title))

    return 0


if __name__ == "__main__":
    sys.exit(main())
