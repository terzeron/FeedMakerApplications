#!/bin/bash

number=41

export PATH=$PATH
FM_HOME=/home/terzeron/workspace/fma
FM_PATH=/home/terzeron/workspace/fm

curl -s -I --retry 3 --retry-delay 120 --retry-max-time 20 --connect-timeout 10 https://newtoki${number}.net/bbs/board.php\?bo_table=webtoon | grep "200 OK" || send_msg_to_line.sh "no service from https://newtoki${number}.net"
