#!/bin/bash
set -e

BUILD_DIR="/tmp/frontend-refresh-$(date +%Y%m%d-%H%M%S)"
FRONTEND_PACKAGE="frontend-with-refresh-token.tar.gz"

echo "Deploying frontend with refresh token support..."

cd /tmp
mkdir -p "$BUILD_DIR"
tar -xzf "$FRONTEND_PACKAGE" -C "$BUILD_DIR"

cd "$BUILD_DIR"

if [ ! -f package.json ]; then
    echo "Error: package.json not found"
    exit 1
fi

echo "Installing dependencies..."
npm install --production=false

echo "Building frontend..."
npm run build

if [ ! -d dist ]; then
    echo "Error: Build failed, dist directory not found"
    exit 1
fi

echo "Deploying to web directory..."
mkdir -p /var/www/novawrite-ai/current
cp -r dist/* /var/www/novawrite-ai/current/
chmod -R 755 /var/www/novawrite-ai/current

echo "Cleaning up..."
rm -rf "$BUILD_DIR"
rm -f "$FRONTEND_PACKAGE"

echo "Frontend deployed successfully!"


