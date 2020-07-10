#!/bin/bash

docker-compose up -d

tmux split-window -v
tmux select-pane -t 0
tmux split-window -v
tmux send-keys "docker logs -f rq_worker_1" C-m
tmux select-pane -t 2
tmux send-keys "docker logs -f video_harvester" C-m


while [ $(docker inspect video_harvester --format='{{.State.Status}}') = "running" ]; do
    sleep 5
done

if [ $(docker inspect video_harvester --format='{{.State.ExitCode}}') = 0 ]; then
    echo "video_harvester exited properly"
else
    echo "There was a problem exiting video_harvester"
fi

# Close the video harvester pane
#tmux send-keys "exit" C-m

sleep 10

while [ 1 = 1 ]; do

    LOG_OUTPUT=$(docker-compose logs --tail 1 rq_worker_1 | tail -n 1)
    TIMESTAMP=$(echo $LOG_OUTPUT | awk '{print $3}')

    if [[ $TIMESTAMP =~ ^[[:digit:]] ]]; then
        
        LAST_LINE_OF_WORKER=$(echo $LOG_OUTPUT | awk -F $TIMESTAMP '{ print $2 }' | awk '{$1=$1};1')

        if [[ $(echo $LAST_LINE_OF_WORKER | grep "Cleaning registries for queue: default") ]] ||\
	       [[ $(echo $LAST_LINE_OF_WORKER | grep "Result is kept for 500 seconds") ]] ||\
	       [[ $(echo $LAST_LINE_OF_WORKER | grep "Listening on default...") ]]; then
            sleep 20

            # After sleeping 30 seconds, make sure that the last line output is still not blank
            LOG_OUTPUT=$(docker-compose logs --tail 1 rq_worker_1 | tail -n 1)
            TIMESTAMP=$(echo $LOG_OUTPUT | awk '{print $3}')

            if [[ $TIMESTAMP =~ ^[[:digit:]] ]]; then

                sleep 15

                LOG_OUTPUT=$(docker-compose logs --tail 1 rq_worker_1 | tail -n 1)
                NEW_TIMESTAMP=$(echo $LOG_OUTPUT | awk '{print $3}')

                if [[ $NEW_TIMESTAMP =~ ^[[:digit:]] ]]; then
                    LAST_LINE_OF_WORKER=$(echo $LOG_OUTPUT | awk -F $NEW_TIMESTAMP '{ print $2 }' | awk '{$1=$1};1')

                    if [[ $(echo $LAST_LINE_OF_WORKER | grep "Cleaning registries for queue: default") ]] ||\
                       [[ $(echo $LAST_LINE_OF_WORKER | grep "Result is kept for 500 seconds") ]] ||\
                       [[ $(echo $LAST_LINE_OF_WORKER | grep "Listening on default...") ]]; then

                        if [[ $TIMESTAMP = $NEW_TIMESTAMP ]]; then
                            break
                        fi
                    fi
                fi
	    fi
        fi
    fi
done

# Close the rq-worker pane
#tmux select-pane -t 1
#tmux send-keys "exit" C-m

docker-compose down

#if [ -d "downloaded" ]; then
#    echo "Syncing files to 8Terr"
#    rsync -av --remove-source-files downloaded/* /44TB/Non\ KG/Drop/NHK/NHK_SHOWS/    
#    echo "Removing downloaded directory"
#    rm -rf downloaded
#else
#    echo "No new files found."
#fi
