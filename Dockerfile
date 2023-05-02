FROM docker
WORKDIR /MisinfoMe
# COPY . /MisinfoMe
COPY docker-compose.web.yml docker-compose.collector.yml common-services.yml /MisinfoMe/
COPY scripts /MisinfoMe/scripts
VOLUME [ "/var/run/docker.sock" ]
VOLUME [ "/MisinfoMe/.env" ]
CMD sh scripts/main.sh
