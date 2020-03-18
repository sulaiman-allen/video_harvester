FROM alpine:edge
#FROM alpine:3.11.3
#FROM alpine:3.7
WORKDIR /usr/src/rq_worker
RUN apk add --no-cache\
        python3\
	py-pip\
        ffmpeg\
        axel\
        chromium\
        chromium-chromedriver\
        libexif\
        udev\
        curl

# This has been updated to make the cache not be used for the following command
RUN head -c 5 /dev/random > random_bytes && curl -L https://yt-dl.org/downloads/latest/youtube-dl -o /usr/local/bin/youtube-dl && chmod a+rx /usr/local/bin/youtube-dl
COPY ./requirements.txt .
#RUN pip3 install --upgrade pip
RUN pip install --upgrade pip
#RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir /usr/lib/chromium-browser && ln -s /usr/lib/chromium/chromedriver /usr/lib/chromium-browser/chromedriver
RUN ln -s /usr/bin/python3 /usr/bin/python
# Copy chromedriver to $PATH
#ENV PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/lib/chromium-browser/"
#RUN echo $PATH
CMD [ "rq", "worker", "-u", "redis://video_harvester_redis:6379" ]
