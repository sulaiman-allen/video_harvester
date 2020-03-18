#!/bin/bash

sed -i s/SELECTED_PARSER=.*/SELECTED_PARSER=nhk/g docker-compose.yml
./get_new_videos.sh
