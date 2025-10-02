#!/bin/bash
# build.sh - Render build script

set -e  # Exit on error

echo "========================================="
echo "ShambaAI Backend - Render Build Script"
echo "========================================="

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Oracle Instant Client (Render-compatible)
echo "Installing Oracle Instant Client..."
if [ ! -d "$HOME/oracle/instantclient_21_12" ]; then
    echo "Downloading Oracle Instant Client..."
    wget -q https://download.oracle.com/otn_software/linux/instantclient/2112000/instantclient-basiclite-linux.x64-21.12.0.0.0dbru.zip -O /tmp/oracle.zip

    echo "Extracting Oracle Instant Client..."
    mkdir -p $HOME/oracle
    unzip -q /tmp/oracle.zip -d $HOME/oracle

    # Set up library path for current session
    export LD_LIBRARY_PATH=$HOME/oracle/instantclient_21_12:$LD_LIBRARY_PATH

    echo "✅ Oracle Instant Client installed"
else
    echo "✅ Oracle Instant Client already installed"
fi

# Set Oracle library path
export LD_LIBRARY_PATH=$HOME/oracle/instantclient_21_12:$LD_LIBRARY_PATH

# Create wallet directory
echo "Creating wallet directory..."
mkdir -p /opt/render/project/src/wallet

# Extract wallet from environment variable (base64 encoded)
if [ ! -z "$ORACLE_WALLET_BASE64" ]; then
    echo "Extracting wallet files..."
    echo "$ORACLE_WALLET_BASE64" | base64 -d > /tmp/wallet.zip
    unzip -q -o /tmp/wallet.zip -d /opt/render/project/src/wallet
    echo "✅ Wallet files extracted"
fi

# Set permissions
chmod -R 644 /opt/render/project/src/wallet/*.ora 2>/dev/null || true
chmod -R 644 /opt/render/project/src/wallet/*.sso 2>/dev/null || true

echo "✅ Build complete!"