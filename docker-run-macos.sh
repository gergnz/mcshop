#!/usr/bin/env bash
docker run --name mcshop -p 5000:5000 -v /var/run/docker.sock.raw:/var/run/docker.sock -v $PWD/minecraft:/srv/minecraft -u501 mcshop
