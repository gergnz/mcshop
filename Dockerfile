FROM python:latest

ARG TARGETARCH

ARG DEBIAN_FRONTEND="noninteractive"
ENV TZ=Australia/Sydney

RUN apt-get update && \
    apt-get dist-upgrade -y && \
    apt-get install -y supervisor

COPY requirements.txt /srv
WORKDIR /srv
RUN pip install -r requirements.txt

COPY . /srv

RUN wget -q "https://caddyserver.com/api/download?os=linux&arch=${TARGETARCH}" -O /srv/caddy && \
    chmod +x /srv/caddy

EXPOSE 5000/tcp
EXPOSE 443/tcp
EXPOSE 80/tcp

CMD ["supervisord","-c","/srv/supervisor.conf"]
