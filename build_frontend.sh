#!/usr/bin/env bash

# go to frontend
pushd frontend
# build the angular app for production mode
ng build --base-href /misinfo/app/ --deploy-url "/misinfo/static/" --prod
popd
# and place the result in the backend static folder ready to be served
rm -rf backend/app
cp -a frontend/dist/frontend backend/app
