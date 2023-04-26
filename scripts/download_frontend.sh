#!/bin/sh
set -e

local=0
remove=0
help=0
BACKEND_DEV_TAG=latest
CREDIBILITY_DEV_TAG=latest
TWITTER_DEV_TAG=latest
CLAIMREVIEW_DEV_TAG=latest

while getopts mh flag
do
    case "${flag}" in
        m) local=1;;
        h) help=1;;
    esac
done

if [ "$help" = "1" ]; then
    echo "Usage: $0 [-m] "
    echo "  -m: download app-dev.zip"
    echo "  -h: help"
    exit 0
fi

cd backend
rm -rf app-v2
mkdir -p app-v2
cd app-v2
if [ "$local" = "1" ]; then
    echo "downloading dev frontend"
    wget https://github.com/MartinoMensio/misinfome-frontend/releases/download/latest/app-dev.zip
    unzip -o app-dev.zip -d .
else
    echo "downloading production frontend"
    wget https://github.com/MartinoMensio/misinfome-frontend/releases/download/latest/app.zip
    unzip -o app.zip -d .
fi
cd ../..