#!/bin/bash
# Fix frontend API configuration in deployed files

cd /var/www/novawrite-ai/current

echo "Fixing API base URL in deployed frontend..."

# Find and replace localhost:8000 with empty string (relative path)
find . -type f \( -name "*.js" -o -name "*.js.map" \) -exec sed -i "s|http://localhost:8000||g" {} \;
find . -type f \( -name "*.js" -o -name "*.js.map" \) -exec sed -i "s|'http://localhost:8000'||g" {} \;
find . -type f \( -name "*.js" -o -name "*.js.map" \) -exec sed -i 's|"http://localhost:8000"||g' {} \;

echo "Frontend API configuration fixed"
echo "Testing..."
curl -I http://127.0.0.1 2>&1 | head -3


