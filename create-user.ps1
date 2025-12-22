# Create user in database
# Usage: .\create-user.ps1

$SERVER = "root@66.154.108.62"
$SERVER_PORT = "22"
$USERNAME = "lanf"
$PASSWORD = "Gauss_234"
$EMAIL = "lanf@example.com"

Write-Host "Creating user in database..." -ForegroundColor Yellow
Write-Host "  Username: $USERNAME" -ForegroundColor Gray
Write-Host "  Email: $EMAIL" -ForegroundColor Gray
Write-Host ""

# Upload and execute the script
ssh -p $SERVER_PORT $SERVER @"
cd /opt/novawrite-ai/backend
source ../venv/bin/activate
python create_user.py $USERNAME $PASSWORD $EMAIL
"@

Write-Host ""
Write-Host "Done!" -ForegroundColor Green


