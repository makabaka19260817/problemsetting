# Git推送脚本 - 多种方法尝试
Write-Host "=== Git推送到GitHub ===" -ForegroundColor Green

# 检查当前状态
Write-Host "`n1. 检查Git状态..." -ForegroundColor Cyan
git status

Write-Host "`n2. 检查网络连接..." -ForegroundColor Cyan
Test-NetConnection -ComputerName github.com -Port 80

Write-Host "`n3. 尝试HTTPS推送..." -ForegroundColor Cyan
$env:GIT_CURL_VERBOSE = 1
git push origin phase1 --verbose

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nHTTPS推送失败，尝试其他方法..." -ForegroundColor Yellow
    
    # 方法2: 强制推送
    Write-Host "`n4. 尝试强制推送..." -ForegroundColor Cyan
    git push -f origin phase1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n强制推送也失败了" -ForegroundColor Red
        
        # 方法3: 显示可能的解决方案
        Write-Host "`n可能的解决方案：" -ForegroundColor Yellow
        Write-Host "1. 使用GitHub Desktop客户端" -ForegroundColor White
        Write-Host "2. 配置VPN或代理" -ForegroundColor White
        Write-Host "3. 使用GitHub CLI: gh repo sync" -ForegroundColor White
        Write-Host "4. 手动上传到GitHub网站" -ForegroundColor White
        
        # 创建项目备份
        Write-Host "`n创建项目备份..." -ForegroundColor Cyan
        $backupName = "project_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"
        Compress-Archive -Path "." -DestinationPath "..\$backupName" -Force
        Write-Host "备份已创建：..\$backupName" -ForegroundColor Green
    }
} else {
    Write-Host "`n推送成功！" -ForegroundColor Green
    git status
}

Write-Host "`n=== 脚本完成 ===" -ForegroundColor Green
