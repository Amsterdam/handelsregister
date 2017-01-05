#!/usr/bin/env bash

set -u   # crash on missing env variables
set -e   # stop on any error

##
echo "clean up old dockers";
docker rm $(docker ps -qa);
echo "clean up completed";

echo "clean up old images";
docker 2>/dev/null 1>&2 rmi `docker images -aq` || true
echo "clean up images completed";

echo "clean up old volumes";
docker volume ls -qf dangling=true | xargs -r docker volume rm;
echo "clean up volumes completed";