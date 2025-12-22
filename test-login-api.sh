#!/bin/bash
# Test login API with proper JSON

cat > /tmp/login-test.json << 'EOF'
{
  "username_or_email": "lanf",
  "password": "Gauss_234"
}
EOF

curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d @/tmp/login-test.json

rm -f /tmp/login-test.json


