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
