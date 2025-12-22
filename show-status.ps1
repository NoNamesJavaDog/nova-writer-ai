# Show deployment status
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Cyan
Write-Host "  Frontend: http://66.154.108.62" -ForegroundColor White
Write-Host "  API: http://66.154.108.62/api" -ForegroundColor White
Write-Host "  API Docs: http://66.154.108.62/api/docs" -ForegroundColor White
Write-Host ""
Write-Host "Service Status:" -ForegroundColor Cyan
ssh -p 22 root@66.154.108.62 "systemctl is-active novawrite-backend nginx postgresql"
Write-Host ""
Write-Host "View details: DEPLOYMENT_COMPLETE.md" -ForegroundColor Yellow
Write-Host ""
