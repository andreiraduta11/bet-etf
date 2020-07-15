#!/usr/bin/env bash


# Stop the application.
docker-compose down --rmi all --volumes --remove-orphans --timeout 30

# Clean all dandling containers, images and volumes.
docker container rm $(docker container ls -aq --filter status=exited) \
  2>/dev/null;
docker image rm $(docker images -f "dangling=true" -q) 2>/dev/null;
docker volume rm $(docker volume ls -f "dangling=true" -q) 2>/dev/null;
