FROM alpine:edge
#FROM alpine:3.11.3
#FROM alpine:3.7

WORKDIR /usr/src/video_harvester

#RUN echo @edge http://nl.alpinelinux.org/alpine/edge/community > /etc/apk/repositories \
    #&& echo @edge http://nl.alpinelinux.org/alpine/edge/main >> /etc/apk/repositories \
    #&& apk add --no-cache \
    #libstdc++@edge \
    #chromium@edge \
    #harfbuzz@edge \
    #nss@edge \
    #chromium-chromedriver@edge \
    #freetype@edge \
    #ttf-freefont@edge \
    #&& rm -rf /var/cache/* \
    #&& mkdir /var/cache/apk

#py-pip is used with edge
RUN apk add --no-cache\
	python3\
	ffmpeg\
	axel\
	libexif\
	udev\
	chromium\
	chromium-chromedriver\
	py-pip\
	curl

# This has been updated to make the cache not be used for the following command
#RUN curl -L :q
RUN head -c 5 /dev/random > random_bytes && curl -L https://yt-dl.org/downloads/latest/youtube-dl -o /usr/local/bin/youtube-dl && chmod a+rx /usr/local/bin/youtube-dl

COPY ./requirements.txt .
#RUN pip3 install --upgrade pip #to be used with non edge builds
RUN pip install --upgrade pip
#RUN pip3 install --no-cache-dir -r requirements.txt #to be used with non edge builds
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir /usr/lib/chromium-browser && ln -s /usr/lib/chromium/chromedriver /usr/lib/chromium-browser/chromedriver
RUN ln -s /usr/bin/python3 /usr/bin/python
# Copy chromedriver to $PATH
#ENV PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/lib/chromium-browser/"
#RUN echo $PATH
RUN chromium-browser --version
CMD [ "python3", "-u", "video_harvester.py" ]
