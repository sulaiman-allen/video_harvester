#!/bin/bash

tmux new -s "get_new_nhk_shows" -d
tmux send-keys -t "get_new_nhk_shows" "./dont_run_directly.sh" C-m
tmux attach -t "get_new_nhk_shows" -d
#tmux split-window -h 'exec docker logs -f rq_worker'
tmux split-window -h 
