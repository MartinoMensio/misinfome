#!/usr/bin/env bash

# go to frontend
pushd frontend
# build the angular app for production mode
ng build --base-href /frontend-v1/ --deploy-url "/frontend-v1/" --prod
popd
# and place the result in the backend static folder ready to be served
rm -rf backend/app-v1
cp -a frontend/dist/frontend backend/app-v1

exit
# Deploy TO KMi server
scp -r frontend/dist/frontend mm35626@kmi-web03.open.ac.uk:/data/user-data/mm35626/MisinfoMe/backend/app-v1
