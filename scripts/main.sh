#!/bin/bash
set -e

help=0
interactive=0

while getopts d:h flag
do
    case "${flag}" in
        h) help=1;;
        i) interactive=1;;
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
    echo "Usage: $0 [-i] [-d misinfome-backend|credibility|twitter-connector|claimreview-collector] [-h]"
    echo "  -i: interactive mode"
    echo "  -d: which submodule is using dev tag (misinfome-backend, credibility, twitter-connector, claimreview-collector, all)"
    echo "  -h: help"
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
    if [ "$interactive" = "1" ]; then
        docker-compose -f docker-compose.web.yml up
    else
        docker-compose -f docker-compose.web.yml up --detach
    fi
elif [ "$COMMAND" = "start.web.dev" ]; then
    echo "Starting web services dev"
    ./scripts/download_frontend.sh -m
    export COMPOSE_PROJECT_NAME=mm35626-web
    docker-compose -f docker-compose.web.yml -f docker-compose.web.dev.yml pull
    if [ "$interactive" = "1" ]; then
        docker-compose -f docker-compose.web.yml -f docker-compose.web.dev.yml up
    else
        docker-compose -f docker-compose.web.yml -f docker-compose.web.dev.yml up --detach
    fi
elif [ "$COMMAND" = "start.collector" ]; then
    echo "Starting collector services"
    export COMPOSE_PROJECT_NAME=mm35626-collector
    docker-compose -f docker-compose.collector.yml pull
    if [ "$interactive" = "1" ]; then
        docker-compose -f docker-compose.collector.yml up
    else
        docker-compose -f docker-compose.collector.yml --detach
    fi
elif [ "$COMMAND" = "start.collector.dev" ]; then
    echo "Starting collector services dev"
    export COMPOSE_PROJECT_NAME=mm35626-collector
    docker-compose -f docker-compose.collector.yml -f docker-compose.collector.yml pull
    if [ "$interactive" = "1" ]; then
        docker-compose -f docker-compose.collector.yml -f docker-compose.collector.yml up up
    else
        docker-compose -f docker-compose.collector.yml -f docker-compose.collector.yml up --detach
    fi
else
    echo "Unknown command: $COMMAND, please set env variable COMMAND to one of start.web, start.web.dev, start.collector, start.collector.dev"
    exit 1
fi
