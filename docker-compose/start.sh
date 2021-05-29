#!/usr/bin/env bash


# Start the application.
docker-compose up --build --force-recreate --always-recreate-deps \
  --remove-orphans

# Introduce a delay to make sure the service has started.
sleep 5

echo "Access the program at http://0.0.0.0:8050"

# xdg-open http://0.0.0.0:8050
