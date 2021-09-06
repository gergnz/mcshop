#!/usr/bin/env bash
docker run --name mcshop \
  -p 5000:5000 \
  -e MC_HOME=/Users/gregc/Scratch/dev/gergnz/mcshop/minecraft/ \
  -e BIND_IP=127.0.0.1 \
  -v /var/run/docker.sock.raw:/var/run/docker.sock \
  -v $PWD/minecraft:/srv/minecraft 
  -u501 mcshop
