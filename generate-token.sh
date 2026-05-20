#!/bin/bash

# Create secrets directory if it doesn't exist
mkdir -p secrets

# Generate a 64-character random hex token
TOKEN=$(openssl rand -hex 32)

# Save to secrets/token
echo "$TOKEN" > secrets/token
chmod 600 secrets/token

echo "Token generated and saved to secrets/token"
echo "Token: $TOKEN"
