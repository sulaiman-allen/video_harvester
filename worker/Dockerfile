FROM alpine:3.7
ENV REDIS_HOST=video_harvester_redis
WORKDIR /usr/src/rq_worker
RUN ls
RUN apk add --no-cache\
        python3\
        ffmpeg\
        axel\
        chromium\
        chromium-chromedriver\
        libexif\
        udev\
        curl

RUN curl -L https://yt-dl.org/downloads/latest/youtube-dl -o /usr/local/bin/youtube-dl && chmod a+rx /usr/local/bin/youtube-dl

COPY ./requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN mkdir /usr/lib/chromium-browser && ln -s /usr/lib/chromium/chromedriver /usr/lib/chromium-browser/chromedriver
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN youtube-dl --version
#RUN youtube-dl -U
COPY youtube-dl /usr/local/bin/youtube-dl

CMD [ "rq", "worker", "-u", "redis://video_harvester_redis:6379" ]
