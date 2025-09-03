#!/usr/bin/env bash

# elements_init.sh
# Stops, removes, and recreates the Elements regtest container
# Sets up default wallet and shell aliases

echo "Stopping and removing previous containers and volumes..."
docker compose down -v

echo "Starting Docker Compose..."
docker compose up -d

# Wait a few seconds for the container to be ready
echo "Waiting for Elements container to initialize..."
sleep 5

# Create default wallet if it doesn't exist
echo "Ensuring default wallet exists..."
docker-compose exec elementsd-regtest elements-cli -chain=regtest -rpcuser=user -rpcpassword=pass getwalletinfo >/dev/null 2>&1 || \
docker-compose exec elementsd-regtest elements-cli -chain=regtest -rpcuser=user -rpcpassword=pass createwallet default

# Add aliases to shell config if not already present
SHELL_RC="$HOME/.zshrc"  # or ~/.bashrc if you use bash
echo "Setting up shell aliases..."
if ! grep -q "alias elements=" "$SHELL_RC"; then
    echo "alias ele='docker-compose exec elementsd-regtest elements-cli -chain=regtest -rpcuser=user -rpcpassword=pass'" >> "$SHELL_RC"
    echo "Aliases added to $SHELL_RC. Run 'source $SHELL_RC' or restart shell to use."
else
    echo "Aliases already present in $SHELL_RC"
fi

echo "Elements regtest setup complete!"
