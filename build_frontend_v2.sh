#!/usr/bin/env bash
set -e

# go to frontend
pushd ../misinfome-frontend-v2
# build the angular app for production mode
# ng build --deploy-url "/frontend-v2/"
ng build --base-href /frontend-v2/
popd
# and place the result in the backend static folder ready to be served
rm -rf backend/app-v2
cp -a ../misinfome-frontend-v2/dist/misinfome-frontend-v2 backend/app-v2


exit
# Deploy TO KMi server
pushd ../misinfome-frontend-v2
ng build --base-href /frontend-v2/
# scp -r ../misinfome-frontend-v2/dist/misinfome-frontend-v2 mm35626@kmi-web03.open.ac.uk:/data/user-data/mm35626/
scp -r ../misinfome-frontend-v2/dist/misinfome-frontend-v2 mm35626@kmi-web03.open.ac.uk:/data/user-data/mm35626/MisinfoMe/backend/app-v2
popd