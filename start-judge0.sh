#!/bin/bash

VERSION="v1.13.1-extra"
DIR_NAME="judge0-$VERSION"
ARCHIVE="$DIR_NAME.zip"
URL="https://github.com/judge0/judge0/releases/download/$VERSION/$ARCHIVE"

generate_password() {
    # Generates a 32-character random alphanumeric string
    LC_ALL=C tr -dc 'a-zA-Z0-9' < /dev/urandom | head -c 32
}

# Download jusge0 if necessary
if [ ! -d "$DIR_NAME" ]; then
    echo "Directory $DIR_NAME not found. Downloading and extracting..."
    wget "$URL"
    unzip "$ARCHIVE"
    rm "$ARCHIVE"
else
    echo "Directory $DIR_NAME already exists. Skipping download."
fi

# Configure judge0
CONF_FILE="$DIR_NAME/judge0.conf"

if [ -f "$CONF_FILE" ]; then
    echo "Updating passwords in $CONF_FILE..."
    
    # Generate passwords
    NEW_REDIS_PASSWORD=$(generate_password)
    NEW_POSTGRES_PASSWORD=$(generate_password)
    
    # Set REDIS_PASSWORD
    sed -i "s/^REDIS_PASSWORD=.*/REDIS_PASSWORD=$NEW_REDIS_PASSWORD/" "$CONF_FILE"
    
    # Set POSTGRES_PASSWORD
    sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_POSTGRES_PASSWORD/" "$CONF_FILE"
    
    echo "Passwords updated successfully."
else
    echo "Error: $CONF_FILE not found."
    exit 1
fi

# Run services
echo "Starting Judge0 services..."
cd "$DIR_NAME" || exit
docker compose up -d db redis
echo "Waiting for database and redis..."
sleep 10s
docker compose up -d
echo "Waiting for remaining services..."
sleep 5s

echo "Judge0 is now running."
