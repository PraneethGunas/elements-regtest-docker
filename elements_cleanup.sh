#!/usr/bin/env bash
# Cleans up all regtest data, wallets, and containers for your Elements setup

set -e

echo "Stopping and removing Docker Compose containers and volumes..."
docker compose down -v

echo "All containers stopped and volumes removed."
echo "Your regtest chain data and wallets are now cleaned."
