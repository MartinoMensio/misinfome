# misinformed_me

## Installation

First of all you need to have the datasets. After that you can do the following:

```bash
git submodule init
git submodule update
```

## Running the system for the first time

`docker-compose up`

in `backend` run `make import_compressed_dump` to load the database from the dump (not provided).

## Make it available to the world

In order to make it available from anywhere, use the following command that will create ssh tunnels:

`ssh -R misinformedme_backend.serveo.net:80:localhost:5000 -R misinformedme.serveo.net:80:localhost:4200 serveo.net`

## If you want to build it without compose (production)

```bash
# create the docker container for mongo
docker run -dit --restart always --name mm34834_mongo -p 127.0.0.1:20001:27017 -v mm34834_mongo_volume:/data/db mongo
# successive times you will simply do
docker start mm34834_mongo

# build the frontend and make it be served by the backend
source build_frontend.sh
# this will place the minified&transpiled frontend in the folder backend/app

# create the docker container for backend (run from the main folder)
docker build -t mm34834/misinfo_server backend
# then create a docker container with that
docker run -dit --restart always --name mm34834_server -p 127.0.0.1:20000:5000 -e MONGO_HOST=mongo:27017 -v `pwd`/backend:/app --link=mm34834_mongo:mongo mm34834/misinfo_server
# successive times just run
docker start mm34834_server

# to import the database in an environment where no mongo commands are installed, run the following
docker run --name mm34834_mongoimporter -v `pwd`/backend/dump:/dump --link=mm34834_mongo:mongo -it mongo bash
# then inside the container run
mongorestore --host mongo --db datasets_resources dump/datasets_resources && echo "restored"
# then exit the container and everything will be fine!
```