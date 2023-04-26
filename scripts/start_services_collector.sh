#!/bin/sh
set -e

local=0
remove=0
help=0
CLAIMREVIEW_DEV_TAG=latest

while getopts mrd:h flag
do
    case "${flag}" in
        m) local=1;;
        r) remove=1;;
        h) help=1;;
        d) case "${OPTARG}" in
            claimreview-collector) CLAIMREVIEW_DEV_TAG=dev;;
            all) CLAIMREVIEW_DEV_TAG=dev;;
        esac;;
    esac
done

if [ "$help" = "1" ]; then
    echo "Usage: $0 [-l] [-r] [-d misinfome-backend|credibility|twitter-connector|claimreview-collector] [-h]"
    echo "  -m: run with source code mapped as volume"
    echo "  -r: remove containers"
    echo "  -d: which submodule is using dev tag (misinfome-backend, credibility, twitter-connector, claimreview-collector)"
    echo "  -h: help"
    exit 0
fi

if [ "$remove" = "1" ]; then
    echo "Removing containers"
    docker rm -f mm35626_claimreview_collector_full mm35626_flaresolverr mm35626_dirtyjson
    if [ "$local" = "1" ]; then
        echo "no mongo local"
    else
        echo "also removing mongo container"
        docker rm -f mm35626_mongo
    fi
    exit 0
fi

echo "Reading .env file"
export $(grep -v '^#' .env | xargs)

echo "Tags:"
echo "  backend: $BACKEND_DEV_TAG"
echo "  credibility: $CREDIBILITY_DEV_TAG"
echo "  twitter-connector: $TWITTER_DEV_TAG"
echo "  claimreview-collector: $CLAIMREVIEW_DEV_TAG"


# mongodb
if [ "$local" = "1" ]; then
    echo "no mongo local"
else
    echo "Starting mongodb"
    docker pull mongo:5
    docker run -dit --restart always \
        --name mm35626_mongo \
        -p 127.0.0.1:27017:27017 \
        -v mm5626_mongo_volume:/data/db \
        mongo:5
fi

# flaresolverr
docker pull ghcr.io/flaresolverr/flaresolverr
docker run -dit --restart always \
  --name=mm35626_flaresolverr \
  -p 127.0.0.1:8191:8191 \
  -e LOG_LEVEL=info \
  --restart unless-stopped \
  ghcr.io/flaresolverr/flaresolverr:latest

### DirtyJSON
docker pull martinomensio/dirtyjson
docker run -dit --restart always \
    --name mm35626_dirtyjson \
    -p 127.0.0.1:12345:12345 \
    martinomensio/dirtyjson

# collector full
docker pull martinomensio/claimreview-collector:$CLAIMREVIEW_DEV_TAG
if [ "$local" = "1" ]; then
    # local full (no auto-restart)
    # mapping the source code as volume overwriting, so can restart and test easily
    docker run -dit --restart always \
        --name mm35626_claimreview_collector_full \
        -p 127.0.0.1:20500:8000 \
        -v `pwd`/claimreview-collector/data:/app/data \
        -e GOOGLE_FACTCHECK_EXPLORER_COOKIE=$GOOGLE_FACTCHECK_EXPLORER_COOKIE \
        -e GITHUB_TOKEN=$GITHUB_TOKEN \
        -v `pwd`/claimreview-collector/claimreview_collector:/app/claimreview_collector \
        --link=mm35626_flaresolverr:flaresolverr \
        -e FLARESOLVERR_HOST=flaresolverr \
        --link=mm35626_mongo:mongo \
        -e MONGO_HOST=mongo:27017 \
        -e MISINFO_BACKEND="http://misinfo_server:5000" \
        --link=mm35626_misinfo_server:misinfo_server \
        -e TWITTER_CONNECTOR="http://misinfo_server:5000/misinfo/api/twitter" \
        -e DIRTYJSON_REST_ENDPOINT="http://dirtyjson_server:12345" \
        --link=mm35626_dirtyjson:dirtyjson_server \
        -e ROLE=full \
        martinomensio/claimreview-collector:$CLAIMREVIEW_DEV_TAG
else
    # server (ROLE=full) without link to twitter_connector, using the public misinfome API. Credibility need for IFCN only (through misinfomeAPI)
    docker run -dit --restart always \
        --name mm35626_claimreview_collector_full \
        -p 127.0.0.1:20500:8000 \
        -e GOOGLE_FACTCHECK_EXPLORER_COOKIE=$GOOGLE_FACTCHECK_EXPLORER_COOKIE \
        -e GITHUB_TOKEN=$GITHUB_TOKEN \
        -v `pwd`/claimreview-collector/data:/app/data \
        --link=mm35626_flaresolverr:flaresolverr \
        -e FLARESOLVERR_HOST=flaresolverr:8191 \
        --link=mm35626_mongo:mongo \
        -e MONGO_HOST=mongo:27017 \
        -e MISINFO_BACKEND="https://misinfo.me" \
        -e TWITTER_CONNECTOR="https://misinfo.me/misinfo/api/twitter" \
        -e DIRTYJSON_REST_ENDPOINT="http://dirtyjson_server:12345" \
        --link=mm35626_dirtyjson:dirtyjson_server \
        -e ROLE=full \
        -e PUBLISH_GITHUB=true \
        martinomensio/claimreview-collector:$CLAIMREVIEW_DEV_TAG
fi
