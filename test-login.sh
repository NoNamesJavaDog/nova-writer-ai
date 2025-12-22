#!/bin/bash
# Test login API

curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username_or_email":"lanf","password":"Gauss_234"}' \
  2>&1


