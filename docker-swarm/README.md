# Usage

## This code should be treated as an example of Docker Swarm Project.

## The functionality of the code may not be complete.

## The PythonAnywhere version is the correct one.

## To start the application:

```bash
# Initialize the swarm.
$ docker swarm init    

# Create the volumes and deploy the stack.
# Use source script.sh instead of ./script.sh because environment variables.
$ source start.sh
```

## For the next steps:

-   Use <http://localhost:3000>, to see statistics about BET, using Grafana.
-   Use <http://localhost:8050>, to calculate your money for each symbol. The table is interactive, so it will re-calculate all the amounts at every change.

## To inspect the status of the services:

```bash
# Running services.
$ docker service ls   

# Logs for a specific service.
$ docker service logs <service_name>

# Running containers. For all containers use --all.
$ docker container ls
```

## To stop the application:

```bash
# Remove the stack and the dandling containers, images and volumes.
$ source stop.sh

# Leave the swarm. If you are the last node or the manager use --force.
$ docker swarm leave

# When you stop using the application consider to remove the volumes.
# !!! This will delete all your persistent storage.
$ sudo rm -rf mysql/lib grafana
```
