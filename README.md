# mcshop
Minecraft Docker Server Management

## Deployment
This container is available in arm64 or amd64 from https://hub.docker.com/r/gergnz/mcshop.

```
docker pull gergnz/mcshop:latest
docker volume create mcshopdb
docker run -d \
-e DOMAIN_HOST=mcshop.example.com \
-e BIND_IP=192.168.1.1 \
-e MC_HOME=/home/user/minecraft \
-v /home/user/minecraft:/srv/minecraft \
-v /var/run/docker.sock:/var/run/docker.sock \
-v mcshopdb:/data \
-p 80:80 \
-p 443:443 \
--privileged \
--name mcshop \
--restart=always \
gergnz/mcshop:latest
```

Then browse to your chose hostname.

First user login is `admin@example.org` password `admin`.

## Development
