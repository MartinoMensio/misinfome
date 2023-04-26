#!/bin/sh

set -e

# update claimreview data
curl -X POST http://localhost:20000/misinfo/api/data/update \
-H 'Content-Type: application/json' \
  -d '{
  "date": "2023_04_25"
}'
# update other data
curl -X POST http://localhost:20300/origins/