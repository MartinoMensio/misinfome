#!/bin/sh
set -e

local=0
remove=0
help=0
BACKEND_DEV_TAG=latest
CREDIBILITY_DEV_TAG=latest
TWITTER_DEV_TAG=latest
CLAIMREVIEW_DEV_TAG=latest

while getopts mrd:h flag
do
    case "${flag}" in
        m) local=1;;
        r) remove=1;;
        h) help=1;;
        d) case "${OPTARG}" in
            misinfome-backend) BACKEND_DEV_TAG=dev;;
            credibility) CREDIBILITY_DEV_TAG=dev;;
            twitter-connector) TWITTER_DEV_TAG=dev;;
            claimreview-collector) CLAIMREVIEW_DEV_TAG=dev;;
            all) BACKEND_DEV_TAG=dev; CREDIBILITY_DEV_TAG=dev; TWITTER_DEV_TAG=dev; CLAIMREVIEW_DEV_TAG=dev;;
        esac;;
    esac
done

if [ "$help" = "1" ]; then
    echo "Usage: $0 [-m] [-r] [-d misinfome-backend|credibility|twitter-connector|claimreview-collector] [-h]"
    echo "  -m: run with source code mapped as volume"
    echo "  -r: remove containers"
    echo "  -d: which submodule is using dev tag (misinfome-backend, credibility, twitter-connector, claimreview-collector, all)"
    echo "  -h: help"
    exit 0
fi

if [ "$remove" = "1" ]; then
    echo "Removing containers"
    docker rm -f mm35626_mongo mm35626_redis mm35626_misinfo_server mm35626_claimreview_collector_light mm35626_credibility mm35626_twitter_connector
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
echo "Starting mongodb"

docker pull mongo:5
docker run -dit --restart always \
    --name mm35626_mongo \
    -p 127.0.0.1:27017:27017 \
    -v mm35626_mongo_volume:/data/db \
    mongo:5

# redis
echo "Starting redis"
docker pull redis
docker run -dit --restart always \
    --name mm35626_redis \
    -p 127.0.0.1:6379:6379 \
    redis

# twitter connector
echo "Starting twitter connector"
docker pull martinomensio/twitter-connector:$TWITTER_DEV_TAG
if [ "$local" = "1" ]; then
    docker run -dit --restart always \
        --name mm35626_twitter_connector \
        -p 127.0.0.1:20200:8000 \
        -v `pwd`/twitter-connector/app:/app/app \
        -e MONGO_HOST=mongo:27017 \
        -e TWITTER_TOKEN_ACADEMIC=$TWITTER_TOKEN_ACADEMIC \
        --link=mm35626_mongo:mongo \
        martinomensio/twitter-connector:$TWITTER_DEV_TAG
else
    docker run -dit --restart always \
        --name mm35626_twitter_connector \
        -p 127.0.0.1:20200:8000 \
        -e MONGO_HOST=mongo:27017 \
        -e TWITTER_TOKEN_ACADEMIC=$TWITTER_TOKEN_ACADEMIC \
        --link=mm35626_mongo:mongo \
        martinomensio/twitter-connector:$TWITTER_DEV_TAG
fi

# claimreview collector
echo "Starting claimreview collector light"
docker pull martinomensio/claimreview-collector:$CLAIMREVIEW_DEV_TAG
if [ "$local" = "1" ]; then
    # local light (no link, using local misinfome). Start before misinfo_server
    # mapping the source code as volume overwriting, so can restart and test easily
    docker run -dit --restart always \
        --name mm35626_claimreview_collector_light \
        -p 127.0.0.1:20400:8000 \
        -v `pwd`/claimreview-collector/data:/app/data \
        -v `pwd`/claimreview-collector/claimreview_collector:/app/claimreview_collector \
        --link=mm35626_mongo:mongo \
        -e MONGO_HOST=mongo:27017 \
        -e ROLE=light \
        martinomensio/claimreview-collector:$CLAIMREVIEW_DEV_TAG
else
    # server web (ROLE=light)
    docker run -dit --restart always \
        --name mm35626_claimreview_collector_light \
        -p 127.0.0.1:20400:8000 \
        -v `pwd`/claimreview-collector/data:/app/data \
        --link=mm35626_mongo:mongo \
        -e MONGO_HOST=mongo:27017 \
        -e ROLE=light \
        martinomensio/claimreview-collector:$CLAIMREVIEW_DEV_TAG
fi

# credibility
echo "Starting credibility"
docker pull martinomensio/credibility:$CREDIBILITY_DEV_TAG
if [ "$local" = "1" ]; then
    docker run -dit --restart always \
    --name mm35626_credibility \
    -p 127.0.0.1:20300:8000 \
    -e MONGO_HOST=mongo:27017 \
    -e MYWOT_USERID=$MYWOT_USERID \
    -e MYWOT_KEY=$MYWOT_KEY \
    -e PINKSLIME_SPREADSHEET_KEY=$PINKSLIME_SPREADSHEET_KEY \
    -v `pwd`/credibility/app:/app/app \
    --link=mm35626_mongo:mongo \
    martinomensio/credibility:$CREDIBILITY_DEV_TAG
else
    # server web
    docker run -dit --restart always \
    --name mm35626_credibility \
    -p 127.0.0.1:20300:8000 \
    -e MONGO_HOST=mongo:27017 \
    -e MYWOT_USERID=$MYWOT_USERID \
    -e MYWOT_KEY=$MYWOT_KEY \
    -e PINKSLIME_SPREADSHEET_KEY=$PINKSLIME_SPREADSHEET_KEY \
    --link=mm35626_mongo:mongo \
    martinomensio/credibility:$CREDIBILITY_DEV_TAG
fi

# frontend
echo "Downloading frontend"
if [ "$local" = "1" ]; then
    # local
    pwd
    ./scripts/download_frontend.sh -m
else
    # server web
    ./scripts/download_frontend.sh
fi

# misinfo-server
echo "Starting misinfo-server"
docker pull martinomensio/misinfome-backend:$BACKEND_DEV_TAG
if [ "$local" = "1" ]; then
    # local
    docker run -dit --restart always \
    --name mm35626_misinfo_server \
    -p 127.0.0.1:20000:5000 \
    -e MONGO_HOST=mongo:27017 \
    -e CREDIBILITY_ENDPOINT=http://credibility:8000 \
    -e TWITTER_CONNECTOR="http://twitter_connector:8000/" \
    -e REDIS_HOST="redis" \
    -e GATEWAY_MODULE_ENDPOINT="https://localhost:1234/test" \
    -e DATA_ENDPOINT="http://claimreview_collector:8000" \
    -e COINFORM_TOKEN=$COINFORM_TOKEN \
    -v `pwd`/backend/api:/app/api \
    -v `pwd`/backend/app-v1:/app/app-v1 \
    -v `pwd`/backend/app-v2:/app/app-v2 \
    --link=mm35626_claimreview_collector_light:claimreview_collector \
    --link=mm35626_mongo:mongo \
    --link=mm35626_credibility:credibility \
    --link=mm35626_twitter_connector:twitter_connector \
    --link=mm35626_redis:redis \
    martinomensio/misinfome-backend:$BACKEND_DEV_TAG
else
    # server web
    docker run -dit --restart always \
    --name mm35626_misinfo_server \
    -p 127.0.0.1:20000:5000 \
    -e MONGO_HOST=mongo:27017 \
    -e CREDIBILITY_ENDPOINT=http://credibility:8000 \
    -e TWITTER_CONNECTOR="http://twitter-connector:8000/" \
    -e REDIS_HOST="redis" \
    -e GATEWAY_MODULE_ENDPOINT="https://localhost:1234/test" \
    -e DATA_ENDPOINT="http://claimreview-collector:8000" \
    -e COINFORM_TOKEN=$COINFORM_TOKEN \
    -v `pwd`/backend/app-v1:/app/app-v1 \
    -v `pwd`/backend/app-v2:/app/app-v2 \
    --link=mm35626_claimreview_collector_light:claimreview-collector \
    --link=mm35626_mongo:mongo \
    --link=mm35626_credibility:credibility \
    --link=mm35626_twitter_connector:twitter-connector \
    --link=mm35626_redis:redis \
    martinomensio/misinfome-backend:$BACKEND_DEV_TAG
fi


# now wait until all containers are up
echo "Waiting for containers to be up"
sleep 10
docker ps