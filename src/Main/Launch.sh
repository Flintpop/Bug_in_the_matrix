#!/bin/bash

killall screen
sleep 2
screen -S watch -dm bash -c 'cd /home/darwho/bug_in_the_matrix/src; python3 watch_tower.py; exec sh'
screen -S main -dm bash -c 'cd /home/darwho/bug_in_the_matrix/src/Main; python3 main.py; exec sh'
sleep 1
screen -r main