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
# local
docker run -dit --restart always --name mongo -p 27017:27017 -v mm34834_mongo_volume:/data/db mongo
# server
docker run -dit --restart always --name mm34834_mongo -p 127.0.0.1:20001:27017 -v mm34834_mongo_volume:/data/db mongo
# successive times you will simply do
docker start mm34834_mongo

# build the frontend and make it be served by the backend
source build_frontend.sh
# this will place the minified&transpiled frontend in the folder backend/app

# create the docker container for backend (run from the main folder)
docker build -t mm34834/misinfo_server backend
# then create a docker container with that
# --> local
docker run -dit --restart always --name mm34834_misinfo_server -p 127.0.0.1:5000:5000 -e MONGO_HOST=mongo:27017 -e CREDIBILITY_ENDPOINT=http://credibility:8000 -e TWITTER_CONNECTOR="http://twitter_connector:8000/" -e REDIS_HOST="redis" -e GATEWAY_MODULE_ENDPOINT="https://localhost:1234/test" -v `pwd`/backend:/app --link=mongo:mongo --link=mm34834_credibility:credibility --link=mm34834_twitter_connector:twitter_connector --link=mm34834_redis:redis mm34834/misinfo_server
# --> server
docker run -dit --restart always --name mm34834_misinfo_server -p 127.0.0.1:20000:5000 -e MONGO_HOST=mongo:27017 -e CREDIBILITY_ENDPOINT=http://credibility:8000 -e TWITTER_CONNECTOR="http://twitter_connector:8000/" -e REDIS_HOST="redis" -e GATEWAY_MODULE_ENDPOINT="https://localhost:1234/test" -v `pwd`/backend:/app --link=mm34834_mongo:mongo --link=mm34834_credibility:credibility --link=mm34834_twitter_connector:twitter_connector --link=mm34834_redis:redis mm34834/misinfo_server
# successive times just run
docker start mm34834_server

# to import the database in an environment where no mongo commands are installed, run the following
docker run --name mm34834_mongoimporter -v `pwd`/backend/dump:/dump --link=mm34834_mongo:mongo -it mongo bash
# then inside the container run
mongorestore --host mongo --db datasets_resources dump/datasets_resources && echo "restored"
# then exit the container and everything will be fine!
```

Start a redis:

```bash
#docker run --restart always -dit --name mm34834_redis -p 6379:6379 --network=twitter_app_default redis ### for local
docker run --restart always -dit --name mm34834_redis -p 6379:6379 redis
```

## Deployment to KMi server

Copy the frontend (from the main folder, after running the `bash ./build_frontend.sh`)
```
scp -r backend/app socsem.kmi.open.ac.uk:/data/user-data/mm35626/MisinfoMe/backend/
```

(create the database dump)
```
pushd backend
make create_compressed_dump
popd
```

Copy the database dump:
```
scp -r backend/dump.tar.gz socsem.kmi.open.ac.uk:/data/user-data/mm35626/MisinfoMe/backend/
```

Extract the database dump (from the KMi server):
```
pushd backend
make extract_dump
popd
```

Import the dump:
```
# to import the database in an environment where no mongo commands are installed, run the following
docker run --rm --name mm34834_mongoimporter -v `pwd`/backend/dump:/dump --link=mm34834_mongo:mongo -it mongo bash
# then inside the container run
mongorestore --host mongo --db datasets_resources dump/datasets_resources && echo "restored"
# then exit the container and everything will be fine!
```

## Apache reverse proxy configuration

Apache configuration

misinfo.me

```
        ## Misinfo Service (mm34834):
        # HTTPS https://cwiki.apache.org/confluence/display/httpd/RewriteHTTPToHTTPS
        RewriteEngine On
        RewriteCond %{HTTPS} !=on
        RewriteRule ^/?(.*) https://%{SERVER_NAME}/$1 [R,L]

        ProxyPass        /misinfo http://127.0.0.1:20000/misinfo
        ProxyPassReverse /misinfo http://127.0.0.1:20000/misinfo
        ProxyPass        / http://127.0.0.1:20000/misinfo
        ProxyPassReverse / http://127.0.0.1:20000/misinfo
        RedirectMatch permanent ^/$ /
        AllowEncodedSlashes NoDecode
```

socsem.kmi.open.ac.uk:

```
        ## Misinfo Service (mm34834):
        # HTTPS https://cwiki.apache.org/confluence/display/httpd/RewriteHTTPToHTTPS
        RewriteEngine On
        RewriteCond %{HTTPS} !=on
        RewriteRule ^/?misinfo/(.*) https://%{SERVER_NAME}/misinfo/$1 [R,L]
        ProxyPass        /misinfo http://127.0.0.1:20000/misinfo
        ProxyPassReverse /misinfo  http://127.0.0.1:20000/misinfo
        RedirectMatch permanent ^/misinfo$ /misinfo
        AllowEncodedSlashes NoDecode


        ## Trivalent misinfo Service (mm34834):
        # HTTPS https://cwiki.apache.org/confluence/display/httpd/RewriteHTTPToHTTPS
        RewriteEngine On
        RewriteCond %{HTTPS} !=on
        RewriteRule ^/?trivalent/(.*) https://%{SERVER_NAME}/trivalent/$1 [R,L]
        ProxyPass        /trivalent http://127.0.0.1:20100/trivalent
        ProxyPassReverse /trivalent  http://127.0.0.1:20100/trivalent
        RedirectMatch permanent ^/trivalent$ /trivalent
```




## Traefik (not used)

Run the orchestrator

docker run -p 80:80 -p 8080:8080 -v /var/run/docker.sock:/var/run/docker.sock traefik --api --docker