sed -i s/SELECTED_PARSER=.*/SELECTED_PARSER=tubi/g docker-compose.yml
./get_new_videos.sh
