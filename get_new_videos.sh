#!/bin/bash

docker-compose up -d

while [ $(docker inspect video_harvester --format='{{.State.Status}}') = "running" ]; do
    sleep 5
done

if [ $(docker inspect video_harvester --format='{{.State.ExitCode}}') = 0 ]; then
    echo "video_harvester exited properly"
else
    echo "There was a problem exiting video_harvester"
fi

sleep 10

while [ 1 = 1 ]; do

    LOG_OUTPUT=$(docker-compose logs --tail 1 rq_worker | tail -n 1)
    TIMESTAMP=$(echo $LOG_OUTPUT | awk '{print $3}')

    #echo "$(date) DEBUG"
    #echo $LOG_OUTPUT

    if [[ $TIMESTAMP =~ ^[[:digit:]] ]]; then
        
        #echo "$(date) LINE FOUND"
        #echo $LOG_OUTPUT

        LAST_LINE_OF_WORKER=$(echo $LOG_OUTPUT | awk -F $TIMESTAMP '{ print $2 }' | awk '{$1=$1};1')
        #echo "OUTER LAST_LINE_OF_WORKER = $LAST_LINE_OF_WORKER"
        if [[ $LAST_LINE_OF_WORKER = "Cleaning registries for queue: default" ]] ||\
	       [[ $LAST_LINE_OF_WORKER = "Result is kept for 500 seconds" ]] ||\
	       [[ $LAST_LINE_OF_WORKER = "*** Listening on default..." ]]; then
            #echo "First condition met"
            sleep 20

            # After sleeping 30 seconds, make sure that the last line output is still not blank
            LOG_OUTPUT=$(docker-compose logs --tail 1 rq_worker | tail -n 1)
            TIMESTAMP=$(echo $LOG_OUTPUT | awk '{print $3}')

            if [[ $TIMESTAMP =~ ^[[:digit:]] ]]; then

                #echo "$(date) INNER LINE FOUND"
                #echo $LOG_OUTPUT
                sleep 15

                LOG_OUTPUT=$(docker-compose logs --tail 1 rq_worker | tail -n 1)
                NEW_TIMESTAMP=$(echo $LOG_OUTPUT | awk '{print $3}')

                if [[ $NEW_TIMESTAMP =~ ^[[:digit:]] ]]; then
                    LAST_LINE_OF_WORKER=$(echo $LOG_OUTPUT | awk -F $NEW_TIMESTAMP '{ print $2 }' | awk '{$1=$1};1')
                    #echo "INNER LAST_LINE_OF_WORKER = $LAST_LINE_OF_WORKER"

                    if [[ $LAST_LINE_OF_WORKER = "Cleaning registries for queue: default" ]] ||\
                       [[ $LAST_LINE_OF_WORKER = "Result is kept for 500 seconds" ]] ||\
                       [[ $LAST_LINE_OF_WORKER = "*** Listening on default..." ]]; then

                        #echo "Second condition met"
                        if [[ $TIMESTAMP = $NEW_TIMESTAMP ]]; then
                            break
                        fi
                    fi
                fi
	        fi
        fi
    fi
done

docker-compose down

if [ -d "downloaded" ]; then
    echo "Syncing files to 8Terr"
    rsync -av --remove-source-files downloaded/* /home/xalerons/8Terr/Non\ KG/Drop/NHK/NHK_SHOWS/    
    echo "Removing downloaded directory"
    rm -rf downloaded
fi
