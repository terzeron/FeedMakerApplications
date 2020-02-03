#/bin/bash

number=26

export PATH=$PATH
FM_HOME=/home/terzeron/workspace/fma
FM_PATH=/home/terzeron/workspace/fm

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

cd $FM_HOME
. $FM_PATH/bin/setup.sh
size=$(python3 $FM_PATH/bin/crawler.py --render-js --sleep 5 --retry 3 https://manamoa${number}.net | wc -c)
[ "$size" -gt 10240 ] || send_msg_to_line.sh "no service from https://manamoa${number}.net"
