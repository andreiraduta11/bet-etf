#!/usr/bin/env bash

# !!! Before running this make sure that the node is already in swarm.
#
# This script will complete all the requirements before running Docker.
# After that, it will deploy the stack to the swarm.
#
# Usage: source start.sh, not ./start.sh!

# Some constants used in script.
export BET_ETF_STACK_NAME="bet_etf_stack"
export BET_ETF_MYSQL_VOLUME="./mysql/lib"
export BET_ETF_GRAFANA_VOLUME="./grafana"

# Prepare the volume for MySQL service.
# !!! mysql/init.sql should exist.
if [ ! -d $BET_ETF_MYSQL_VOLUME ]; then
  mkdir -p $BET_ETF_MYSQL_VOLUME
fi

# Prepare the volume for Grafana service.
if [ ! -d $BET_ETF_GRAFANA_VOLUME ]; then
  mkdir -p $BET_ETF_GRAFANA_VOLUME
fi
sudo chown -R 472:472 $BET_ETF_GRAFANA_VOLUME

docker build --force-rm --rm --tag etf_bet_application application
docker build --force-rm --rm --tag etf_bet_collector collector
docker build --force-rm --rm --tag etf_bet_visualizer visualizer

# Deploy the stack on the swarm.
docker stack deploy --prune --compose-file stack.yml $BET_ETF_STACK_NAME
