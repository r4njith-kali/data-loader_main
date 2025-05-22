#!/bin/sh

docker build --file Dockerfile_Cron --tag data_loader:latest .
docker image prune