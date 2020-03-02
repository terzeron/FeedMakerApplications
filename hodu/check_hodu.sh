#!/bin/bash

number=20

export PATH=$PATH
FM_HOME=/home/terzeron/workspace/fma
FM_PATH=/home/terzeron/workspace/fm

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

cd $FM_HOME
. $FM_PATH/bin/setup.sh

size=$(python $FM_PATH/bin/crawler.py --render-js=false --sleep=5 --retry=3 https://hodu${number}.net | wc -c)
[ "$size" -gt 10240 ] || \
    (send_msg_to_line.sh "no service from https://hodu${number}.net"; \
     send_msg_to_line.sh "would you check the new site? https://hodu$((number+1)).net")
