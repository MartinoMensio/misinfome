#!/bin/bash
set -e

help=0

while getopts d:h flag
do
    case "${flag}" in
        h) help=1;;
        d) case "${OPTARG}" in
            misinfome-backend) export BACKEND_TAG=dev;;
            credibility) export CREDIBILITY_TAG=dev;;
            twitter-connector) export TWITTER_CONNECTOR_TAG=dev;;
            claimreview-collector) export CLAIMREVIEW_COLLECTOR_TAG=dev;;
            all) export BACKEND_TAG=dev; export CREDIBILITY_TAG=dev; export TWITTER_CONNECTOR_TAG=dev; export CLAIMREVIEW_COLLECTOR_TAG=dev;;
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
echo "  backend: $BACKEND_TAG"
echo "  credibility: $CREDIBILITY_TAG"
echo "  twitter-connector: $TWITTER_CONNECTOR_TAG"
echo "  claimreview-collector: $CLAIMREVIEW_COLLECTOR_TAG"


if [ "$COMMAND" = "start.web" ]; then
    echo "Starting web services"
    ./scripts/download_frontend.sh
    export COMPOSE_PROJECT_NAME=mm35626-web
    docker-compose -f docker-compose.web.yml pull
    docker-compose -f docker-compose.web.yml up
elif [ "$COMMAND" = "start.web.dev" ]; then
    echo "Starting web services dev"
    ./scripts/download_frontend.sh -m
    export COMPOSE_PROJECT_NAME=mm35626-web
    docker-compose -f docker-compose.web.yml -f docker-compose.web.dev.yml pull
    docker-compose -f docker-compose.web.yml -f docker-compose.web.dev.yml up
elif [ "$COMMAND" = "start.collector" ]; then
    echo "Starting collector services"
    export COMPOSE_PROJECT_NAME=mm35626-collector
    docker-compose -f docker-compose.collector.yml pull
    docker-compose -f docker-compose.collector.yml up
elif [ "$COMMAND" = "start.collector.dev" ]; then
    echo "Starting collector services dev"
    export COMPOSE_PROJECT_NAME=mm35626-collector
    docker-compose -f docker-compose.collector.yml -f docker-compose.collector.yml pull
    docker-compose -f docker-compose.collector.yml -f docker-compose.collector.yml up
else
    echo "Unknown command: $COMMAND, please set env variable COMMAND to one of start.web, start.web.dev, start.collector, start.collector.dev"
    exit 1
fi
