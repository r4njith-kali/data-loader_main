#!/bin/sh

# Run this shell script to build a docker image for M13
# If there's any problem with the Dockerfile/dependencies, this will not succeed
REGISTRY=registry-sg.cloud.hyundai-autoever.com
IMAGE=$REGISTRY/data_science_application/cm_siemens_data_loader
VERSION=0.0.4

# Build docker image locally
docker build \
    -f Dockerfile_Cron \
    --platform=linux/amd64 \
    -t $IMAGE:$VERSION .

# Check if the image build was successful
if [ $? -ne 0 ]; then
    echo "Docker build failed. Exiting."
    exit 1
fi

# Read username and password from JSON file
credentials=$(cat ./.secrets/credentials.json)
un=$(echo "$credentials" | jq -r '.Harbor.username')
pd=$(echo "$credentials" | jq -r '.Harbor.password')

# Login to the registry
docker login $REGISTRY -u "$un" -p "$pd"

# Check if the login was successful
if [ $? -ne 0 ]; then
    echo "Docker login failed. Exiting."
    exit 1
fi

# Push the image to Harbor
docker push $IMAGE:$VERSION

# Check if the push was successful
if [ $? -ne 0 ]; then
    echo "Docker push failed. Exiting."
    exit 1
fi

echo "Program elapsed"
echo "Image: $IMAGE, Version: $VERSION"