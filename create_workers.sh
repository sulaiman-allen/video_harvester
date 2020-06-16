#!/bin/bash



WORKERS=""

function clear_old_workers() {
  sed -i '/Workers_Begin/,/Workers_End/{//!d}' docker-compose.yml
}

function build_workers() {
  for i in $(seq 1); do
    rq_worker="rq_worker_$i"
    TEMPLATE="
  $rq_worker: 
    container_name: rq_worker_$i
    image: glorbon_labs/rq_worker:latest
    volumes:
      - ${USERDIR}/docker/video_harvester:/usr/src/rq_worker
      - /dev/shm:/dev/shm
    user: "1000:1000"
    environment:
      - REDIS_HOST=video_harvester
      - PUID=1000
      - PGID=1000
      - SELECTED_PARSER=nhk
      - PYTHONUNBUFFERED=1
    depends_on:
      - video_harvester_redis
  "	
  WORKERS="${WORKERS} ${TEMPLATE}"
  done
  printf "$WORKERS"
}

clear_old_workers

WORKERS=$(build_workers)

preprocessed_VAR=$(printf '%s\n' "$WORKERS" |
  sed 's/\\/&&/g;s/^[[:blank:]]/\\&/;s/$/\\/')

sed -i -e "/Workers_Begin/a\\
${preprocessed_VAR%?}" docker-compose.yml

