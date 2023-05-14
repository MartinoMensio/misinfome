# MisinfoMe

## Archictecture

This project has two main deployments: 
- **collector**: collects/updates the dataset
- **web**: serves the MisinfoMe app

```code
          collector                            web
┌────────────────────────────┐    ┌─────────────────────────────┐
│ claimreview_collector_full │    │       misinfo_server        │
│         port:20500         │    │         port:20000          │
├────────────────────────────┤    ├─────────────────────────────┤
|        flaresolverr        │    │      twitter_connector      │
|         port: 8191         │    │         port:20200          │
├────────────────────────────┤    ├─────────────────────────────┤
|         dirtyjson          │    │         credibility         │
|         port:12345         │    │         port:20300          │
├────────────────────────────┤    ├─────────────────────────────┤
|            mongo           │    │ claimreview_collector_light │
|         port:20600         │    │         port:20400          │
└────────────────────────────┘    ├─────────────────────────────┤
                                  │            mongo            │
                                  │          port:20700         │
                                  └─────────────────────────────┘
```

The declaration is implemented with the scripts `scripts/start_services_web.sh` and `scripts/start_services_cllectr.sh`.

### Collector
This deployment is updating every day the dataset and uploading it to a daily release stored on the [claimreview-data](https://github.com/MartinoMensio/claimreview-data) repository, named with the format `YYYY_MM_DD`.

The container `claimreview_collector_full` is an instance of the [claimreview-collector](https://github.com/MartinoMensio/claimreview-collector) docker image and is configured with environment variables:
- `ROLE=full`: enables the daily update
- `PUBLISH_GITHUB=true`: to enable publishing data to GitHub
- `GITHUB_TOKEN`: to enable publishing data to GitHub
- `GOOGLE_FACTCHECK_EXPLORER_COOKIE`: needed to collect from Google Fact-check Explorer
- `FLARESOLVERR_HOST`: where to find the instance of flaresolverr (to collect from websites and avoid captchas)
- `DIRTYJSON_REST_ENDPOINT`: where to find dirtyjson microservice
- `MONGO_HOST`: where to find mongodb (to store data)
- `MISINFO_BACKEND`: where to find the public web API (to use the unshorten API)
- `TWITTER_CONNECTOR`: where to find the connector to twitter API

Flaresolverr is used to avoid the captchas.
Dirtyjson is used to fix some broken jsons.
Mongo is used to store data.

### Web

The web deployment is more elaborated. It is made of a frontend and many microservices.

The main container is `misinfo_server` that is an instance of [misinfome-backend](https://github.com/MartinoMensio/misinfome-backend) that acts as public API and also serves the frontend.

Twitter microservice `twitter_connector` is responsible to retrieve timelines, users, tweets.

Credibility microservice `credibility` computes aggregated scores of credibility.

Claimreview microservice `claimreview_collector_light` provides access to the data


## Installation


- get access tokens and create .env file
- start the two deployments
- init database for web


Docker-compose
```bash
# without docker-compose installed
docker build . -t martinomensio/misinfome
# run docker-compose image that will do the same:
# - mount /var/run/docker.sock to give control of docker
# - mount .env file that contains all the env variables with secrets
# - CLAIMREVIEW_DATA_PATH: pass the host data path so that the container know where it is to run docker-compose
# - COMMAND can be start.web or start.collector

# web
docker run -it --name mm35626_misinfome \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v `pwd`/.env:/MisinfoMe/.env \
        -e CLAIMREVIEW_DATA_PATH=`pwd`/claimreview-collector/data \
        -v `pwd`/backend/app-v2:/MisinfoMe/backend/app-v2 \
        -e FRONTEND_V1_PATH=`pwd`/backend/app-v1 \
        -e FRONTEND_V2_PATH=`pwd`/backend/app-v2 \
        -e INTERACTIVE=1 \
        -e COMMAND=start.web \
        martinomensio/misinfome

# collector
docker run -it --name mm35626_misinfome \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v `pwd`/.env:/MisinfoMe/.env \
        -e CLAIMREVIEW_DATA_PATH=`pwd`/claimreview-collector/data \
        -e INTERACTIVE=1 \
        -e COMMAND=start.collector \
        martinomensio/misinfome

# with docker-compose installed
COMMAND=start.web bash scripts/main.sh
COMMAND=start.web.dev bash scripts/main.sh
COMMAND=start.web TWITTER_CONNECTOR_TAG=dev bash scripts/main.sh
COMMAND=start.collector bash scripts/main.sh
COMMAND=start.collector.dev bash scripts/main.sh
COMMAND=start.collector TWITTER_CONNECTOR_TAG=dev bash scripts/main.sh
```

TODOs:
- copy volumes before deploy (mm35626_mongo_volume to mm35626_web_mongo_volume and mm35626_collector_mongo_volume)


## Auto-update

The submodules self-update the dependencies to avoid security vulnerabilities, and if successful they update the main repository to merge the changes.

- every week each submodule runs a github action that updates the dependencies, runs tests, rebuilds the docker image and tags it as `dev`
- the submodule notifies the main repository
- the main repository performs integration tests, updates the submodule and adds the tag `latest` to the docker images

The frontend instead is built and stored as an artifact, and deployed with the `scripts/download_frontend.sh` script.

## Apache reverse proxy configuration

Apache configuration

misinfo.me

```
        # section :80
        ## Misinfo Service (mm35626):
        # HTTPS https://cwiki.apache.org/confluence/display/httpd/RewriteHTTPToHTTPS
        RewriteEngine On
        RewriteCond %{HTTPS} !=on
        RewriteRule ^/?(.*) https://%{SERVER_NAME}/$1 [R,L]


        ProxyPass        / http://127.0.0.1:20000/
        ProxyPassReverse / http://127.0.0.1:20000/
        AllowEncodedSlashes NoDecode


        # section :443
        ## Misinfo Service (mm35626):
        #RewriteEngine on
        #ProxyPass        / http://127.0.0.1:20000/
        #ProxyPassReverse / http://127.0.0.1:20000/
        AllowEncodedSlashes NoDecode
```
sudo systemctl restart httpd.service
