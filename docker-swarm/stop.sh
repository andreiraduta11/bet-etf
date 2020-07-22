#!/usr/bin/env bash

# This script will remove the docker stack.
# It uses the environment variable ETF_BET_STACK_NAME, so remeber to use
# source script.sh, not ./script.sh.

# Introduce a delay to be sure that the stack is removed.
docker stack rm $BET_ETF_STACK_NAME;
sleep 15

# Remove the dandling containers, images and volumes.
# Do not show errors, when no dandling object exist.
docker container rm $(docker container ls -aq --filter status=exited) \
  2>/dev/null;
docker image rm $(docker images -f "dangling=true" -q) 2>/dev/null;
docker volume rm $(docker volume ls -f "dangling=true" -q) 2>/dev/null;
