# API 测试脚本
param(
    [string]$BaseUrl = "http://66.154.108.62"
)

$ErrorActionPreference = "Continue"

Write-Host "🧪 开始测试 API 接口..." -ForegroundColor Cyan
Write-Host "基础URL: $BaseUrl`n" -ForegroundColor Gray

$testResults = @()

# 测试函数
function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers = @{},
        [string]$Body = $null,
        [int]$ExpectedStatus = 200
    )
    
    try {
        $params = @{
            Method = $Method
            Uri = $Url
            Headers = $Headers
            ContentType = "application/json"
        }
        
        if ($Body) {
            $params.Body = $Body
        }
        
        $response = Invoke-RestMethod @params -ErrorAction Stop
        $statusCode = 200
        
        $testResults += [PSCustomObject]@{
            Name = $Name
            Status = "✅ 通过"
            StatusCode = $statusCode
            Message = "成功"
        }
        
        Write-Host "✅ $Name - 通过" -ForegroundColor Green
        return $true
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorMsg = $_.Exception.Message
        
        $testResults += [PSCustomObject]@{
            Name = $Name
            Status = "❌ 失败"
            StatusCode = $statusCode
            Message = $errorMsg
        }
        
        Write-Host "❌ $Name - 失败 (状态码: $statusCode)" -ForegroundColor Red
        Write-Host "   错误: $errorMsg" -ForegroundColor Yellow
        return $false
    }
}

# 1. 测试健康检查
Write-Host "`n📋 测试 1: 健康检查端点" -ForegroundColor Yellow
Test-Endpoint -Name "健康检查" -Method "GET" -Url "$BaseUrl/api/health" -ExpectedStatus 200

# 2. 测试登录（需要先注册或使用测试账号）
Write-Host "`n📋 测试 2: 认证端点" -ForegroundColor Yellow
$loginBody = @{
    username = "testuser"
    password = "testpass123"
} | ConvertTo-Json

$loginResult = Test-Endpoint -Name "登录" -Method "POST" -Url "$BaseUrl/api/auth/login" -Body $loginBody -ExpectedStatus 200

$token = $null
if ($loginResult) {
    try {
        $loginResponse = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/auth/login" -Body $loginBody -ContentType "application/json"
        if ($loginResponse.access_token) {
            $token = $loginResponse.access_token
            Write-Host "   获取到访问令牌" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "   无法获取访问令牌，跳过需要认证的测试" -ForegroundColor Yellow
    }
}

# 3. 测试需要认证的端点（如果有token）
if ($token) {
    $authHeaders = @{
        "Authorization" = "Bearer $token"
    }
    
    Write-Host "`n📋 测试 3: 需要认证的端点" -ForegroundColor Yellow
    
    # 测试获取小说列表
    Test-Endpoint -Name "获取小说列表" -Method "GET" -Url "$BaseUrl/api/novels" -Headers $authHeaders
    
    # 测试任务端点
    Test-Endpoint -Name "获取活跃任务" -Method "GET" -Url "$BaseUrl/api/tasks/active" -Headers $authHeaders
}

# 4. 测试前端页面
Write-Host "`n📋 测试 4: 前端页面" -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/" -Method GET -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        $testResults += [PSCustomObject]@{
            Name = "前端首页"
            Status = "✅ 通过"
            StatusCode = 200
            Message = "成功加载"
        }
        Write-Host "✅ 前端首页 - 通过" -ForegroundColor Green
    }
}
catch {
    $testResults += [PSCustomObject]@{
        Name = "前端首页"
        Status = "❌ 失败"
        StatusCode = $_.Exception.Response.StatusCode.value__
        Message = $_.Exception.Message
    }
    Write-Host "❌ 前端首页 - 失败" -ForegroundColor Red
}

# 输出测试结果摘要
Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "📊 测试结果摘要" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

$passed = ($testResults | Where-Object { $_.Status -eq "✅ 通过" }).Count
$failed = ($testResults | Where-Object { $_.Status -eq "❌ 失败" }).Count
$total = $testResults.Count

Write-Host "`n总计: $total" -ForegroundColor White
Write-Host "通过: $passed ✅" -ForegroundColor Green
Write-Host "失败: $failed ❌" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })

Write-Host "`n详细结果:" -ForegroundColor Cyan
$testResults | Format-Table -AutoSize

if ($failed -eq 0) {
    Write-Host "`n🎉 所有测试通过！" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "`n⚠️ 部分测试失败，请检查服务器状态" -ForegroundColor Yellow
    exit 1
}

