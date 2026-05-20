#!/bin/bash

DIR_NAME="judge0"

generate_password() {
    # Generates a 32-character random alphanumeric string
    LC_ALL=C tr -dc 'a-zA-Z0-9' < /dev/urandom | head -c 32
}

if [ ! -d "$DIR_NAME" ]; then
    echo "Error: $DIR_NAME directory not found."
    exit 1
fi

# Configure judge0
CONF_FILE="$DIR_NAME/judge0.conf"

# Generate passwords if they are empty
REDIS_PWD=$(grep "^REDIS_PASSWORD=" "$CONF_FILE" | cut -d'=' -f2)
POSTGRES_PWD=$(grep "^POSTGRES_PASSWORD=" "$CONF_FILE" | cut -d'=' -f2)

if [ -z "$REDIS_PWD" ]; then
    echo "Generating Redis password..."
    NEW_REDIS_PASSWORD=$(generate_password)
    sed -i "s/^REDIS_PASSWORD=.*/REDIS_PASSWORD=$NEW_REDIS_PASSWORD/" "$CONF_FILE"
fi

if [ -z "$POSTGRES_PWD" ]; then
    echo "Generating Postgres password..."
    NEW_POSTGRES_PASSWORD=$(generate_password)
    sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_POSTGRES_PASSWORD/" "$CONF_FILE"
fi

# Run services
echo "Starting Judge0 services..."
cd "$DIR_NAME" || exit

# Start DB and Redis first
docker compose up -d db redis
echo "Waiting for database and redis..."
sleep 10s

# Start the rest
docker compose up -d
echo "Waiting for services to initialize..."
sleep 10s

echo "Judge0 is now running."
