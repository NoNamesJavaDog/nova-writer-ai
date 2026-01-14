# 查看后端日志的便捷脚本

Write-Host "=== NovaWrite AI 后端日志查看工具 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 实时日志 (按Ctrl+C退出)" -ForegroundColor Yellow
Write-Host "2. 最近100条日志" -ForegroundColor Yellow
Write-Host "3. 最近的错误日志" -ForegroundColor Yellow  
Write-Host "4. 应用错误日志文件" -ForegroundColor Yellow
Write-Host "5. 应用普通日志文件" -ForegroundColor Yellow
Write-Host "6. 查看服务状态" -ForegroundColor Yellow
Write-Host ""

$choice = Read-Host "请选择 (1-6)"

switch ($choice) {
    "1" {
        Write-Host "按 Ctrl+C 退出..." -ForegroundColor Green
        ssh root@66.154.108.62 "journalctl -u novawrite-backend -f"
    }
    "2" {
        ssh root@66.154.108.62 "journalctl -u novawrite-backend -n 100 --no-pager"
    }
    "3" {
        ssh root@66.154.108.62 "journalctl -u novawrite-backend -p err -n 50 --no-pager"
    }
    "4" {
        ssh root@66.154.108.62 "tail -100 /opt/novawrite-ai/logs/backend.error.log"
    }
    "5" {
        ssh root@66.154.108.62 "tail -100 /opt/novawrite-ai/logs/backend.log"
    }
    "6" {
        ssh root@66.154.108.62 "systemctl status novawrite-backend --no-pager"
    }
    default {
        Write-Host "无效选择" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== 常用命令 ===" -ForegroundColor Cyan
Write-Host "查看最近日志: ssh root@66.154.108.62 'journalctl -u novawrite-backend -n 50'" -ForegroundColor Gray
Write-Host "实时日志:     ssh root@66.154.108.62 'journalctl -u novawrite-backend -f'" -ForegroundColor Gray
Write-Host "重启服务:     ssh root@66.154.108.62 'systemctl restart novawrite-backend'" -ForegroundColor Gray

