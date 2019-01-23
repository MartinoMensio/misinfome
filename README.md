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
