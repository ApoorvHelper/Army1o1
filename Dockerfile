FROM python:3.8-slim as builder

RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    libssl-dev \
    libffi-dev

COPY mustinstall.txt .

RUN pip install --prefix /install --no-warn-script-location --no-cache-dir -r mustinstall.txt

FROM python:3.8-slim

RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

ARG config_dir=/config
RUN mkdir -p $config_dir
VOLUME $config_dir
ENV CONFIG_VOLUME=$config_dir

ARG username=''
ENV ARMY1O1_USER=$username
ARG password=''
ENV ARMY1O1_PASS=$password

ARG proxyuser=''
ENV ARMY1O1_PROXY_USER=$proxyuser
ARG proxypass=''
ENV ARMY1O1_PROXY_PASS=$proxypass
ARG proxytype=''
ENV ARMY1O1_PROXY_TYPE=$proxytype
ARG proxyloc=''
ENV ARMY1O1_PROXY_LOC=$proxyloc

ARG army1o1_dotenv=''
ENV ARMY1O1_DOTENV=$army1o1_dotenv

ARG use_https=''
ENV HTTPS_ONLY=$use_https

ARG army1o1_port=5000
ENV EXPOSE_PORT=$army1o1_port

ARG twitter_alt=''
ENV ARMY1O1_ALT_TW=$twitter_alt
ARG youtube_alt=''
ENV ARMY1O1_ALT_YT=$youtube_alt
ARG instagram_alt=''
ENV ARMY1O1_ALT_IG=$instagram_alt
ARG reddit_alt=''
ENV ARMY1O1_ALT_RD=$reddit_alt
ARG medium_alt=''
ENV ARMY1O1_ALT_MD=$medium_alt
ARG translate_alt=''
ENV ARMY1O1_ALT_TL=$translate_alt

WORKDIR /army1o1

COPY --from=builder /install /usr/local
COPY software/ software/
COPY run .
RUN chown 102:102 software/static/build

EXPOSE $EXPOSE_PORT

HEALTHCHECK  --interval=30s --timeout=5s \
  CMD curl -f http://localhost:${EXPOSE_PORT}/healthz || exit 1

CMD ./run
