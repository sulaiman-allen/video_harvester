#!/bin/bash

show_help() {
# Displays a help menu.

    printf "
        --parser, -p:                     Choose parser. Currently nhk or tubi
        --num_of_workers, -n:             Choose number of rq_workers. If not selected, this will default to 2.
	--max_workers_for_system, -m:     Choose to create as many workers as there are processor cores available on the system.
        --help, -h:                       Display this menu.\n\n"

    exit 1
}


function build_workers() {
  for i in $(seq $NUM_OF_WORKERS); do
    rq_worker="rq_worker_$i"
    TEMPLATE="
  $rq_worker: 
    container_name: rq_worker_$i
    image: glorbon_labs/rq_worker:latest
    volumes:
      - ${USERDIR}/docker/video_harvester:/usr/src/rq_worker
      - /dev/shm:/dev/shm
    user: \"$LOCAL_UID:$LOCAL_GID\"
    environment:
      - REDIS_HOST=video_harvester
      - PUID=$LOCAL_UID
      - PGID=$LOCAL_GID
      - SELECTED_PARSER=$PARSER
      - PYTHONUNBUFFERED=1
    depends_on:
      - video_harvester_redis
  "	
    WORKERS="${WORKERS} ${TEMPLATE}"
  done

  printf "$WORKERS"
}

# If the user ran the program with no arguments
if [ -z $1 ]; then
	NUM_OF_WORKERS=2
	PARSER="nhk"
else
	while :; do
	    case $1 in
		-h|--help)
		    show_help
		    ;;
		-p|--parser)
		    PARSER=$2
		    shift
		    ;;
		-n|--num_of_workers)
		    NUM_OF_WORKERS=$2
		    shift
		    ;;
		-m|--max_workers_for_system)
		    NUM_OF_WORKERS=$(lscpu | grep ^CPU\(s\) | awk '{print $2}')
		    ;;
		*) # Default case: No more options, so break out of the loop.
		    if [ -z $NUM_OF_WORKERS ]; then
			NUM_OF_WORKERS=2
	 	    fi

		    if [ -z $PARSER ]; then
			PARSER="nhk"
		    fi
		    break
	    esac
	    shift
	done
fi

echo "Number of workers = $NUM_OF_WORKERS"
echo "Parser = $PARSER"
LOCAL_UID=$(id | awk '{print $1}' | grep -m 1 -oP 'uid=\K[^\(]*')
LOCAL_GID=$(id | awk '{print $2}' | grep -m 1 -oP 'gid=\K[^\(]*')
USERDIR=$HOME

WORKERS=$(build_workers)

FLEET=$(printf '%s\n' "$WORKERS" |
  sed 's/\\/&&/g;s/^[[:blank:]]/\\&/;s/$/\\/')

sed -e "/Workers_Begin/a\\
${FLEET%?}" docker-compose-template.yml > docker-compose.yml

export NUM_OF_WORKERS
export PARSER

