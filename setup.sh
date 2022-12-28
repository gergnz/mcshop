#!/usr/bin/env bash
if [ ! -f /data/db.sqlite ]
then
  cp /srv/empty.db /data/db.sqlite
fi

rm -f /srv/mcshop/db.sqlite
rm -f /srv/instance/db.sqlite
mkdir -p /srv/instance
ln -s /data/db.sqlite /srv/mcshop/db.sqlite
ln -s /data/db.sqlite /srv/instance/db.sqlite
mkdir -p /root/.local/share
ln -s /data/caddy /root/.local/share/
