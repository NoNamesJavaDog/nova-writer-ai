#!/bin/bash
set -e

BUILD_DIR="/tmp/frontend-chapter-fix-$(date +%Y%m%d-%H%M%S)"
FRONTEND_PACKAGE="frontend-chapter-fix.tar.gz"

echo "Deploying frontend with chapter sync fix..."

cd /tmp
mkdir -p "$BUILD_DIR"
tar -xzf "$FRONTEND_PACKAGE" -C "$BUILD_DIR"

# Find the frontend source directory
SOURCE_DIR=""
if [ -d "frontend-outline-fix-*" ]; then
    SOURCE_DIR=$(ls -td frontend-outline-fix-* 2>/dev/null | head -1)
fi
if [ -z "$SOURCE_DIR" ] && [ -d "frontend-build-*" ]; then
    SOURCE_DIR=$(ls -td frontend-build-* 2>/dev/null | head -1)
fi

if [ -z "$SOURCE_DIR" ] || [ ! -f "$SOURCE_DIR/package.json" ]; then
    echo "No frontend source found, need full rebuild..."
    echo "Please rebuild frontend from source"
    rm -rf "$BUILD_DIR"
    rm -f "$FRONTEND_PACKAGE"
    exit 1
fi

echo "Found frontend source: $SOURCE_DIR"
cd "$SOURCE_DIR"

# Copy the fixed file
if [ -f "$BUILD_DIR/services/apiService.ts" ]; then
    cp "$BUILD_DIR/services/apiService.ts" novawrite-ai---professional-novel-assistant/services/apiService.ts 2>/dev/null || cp "$BUILD_DIR/services/apiService.ts" services/apiService.ts 2>/dev/null || true
fi

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

echo "Frontend chapter sync fix deployed successfully!"


