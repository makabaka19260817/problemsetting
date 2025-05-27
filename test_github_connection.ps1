#!/usr/bin/env powershell
# 网络连接和GitHub推送测试脚本

Write-Host "🌐 GitHub 连接测试工具" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green

function Test-GitHubConnection {
    Write-Host "`n🔍 正在测试GitHub连接..." -ForegroundColor Yellow
    
    try {
        $result = Test-NetConnection -ComputerName "github.com" -Port 443 -InformationLevel Quiet
        if ($result) {
            Write-Host "✅ GitHub连接正常 (端口443可达)" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ GitHub连接失败 (端口443不可达)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ 网络测试出错: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-GitStatus {
    Write-Host "`n📊 检查Git仓库状态..." -ForegroundColor Yellow
    
    try {
        $status = git status --porcelain
        if ($status) {
            Write-Host "⚠️  有未提交的更改" -ForegroundColor Yellow
            git status
        } else {
            Write-Host "✅ 工作目录干净" -ForegroundColor Green
        }
        
        $ahead = git rev-list --count origin/phase1..HEAD
        if ($ahead -gt 0) {
            Write-Host "📤 有 $ahead 个提交等待推送" -ForegroundColor Cyan
        } else {
            Write-Host "✅ 与远程仓库同步" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ Git状态检查失败: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Start-GitHubPush {
    Write-Host "`n🚀 尝试推送到GitHub..." -ForegroundColor Yellow
    
    try {
        git push origin phase1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 推送成功！" -ForegroundColor Green
            Write-Host "🎉 您的代码已成功提交到GitHub！" -ForegroundColor Green
            Write-Host "📍 仓库地址: https://github.com/makabaka19260817/problemsetting" -ForegroundColor Cyan
            return $true
        } else {
            Write-Host "❌ 推送失败，请检查网络连接或认证信息" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ 推送出错: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Show-NextSteps {
    Write-Host "`n📋 GitHub发布后续步骤:" -ForegroundColor Cyan
    Write-Host "1. 访问: https://github.com/makabaka19260817/problemsetting" -ForegroundColor White
    Write-Host "2. 创建Pull Request (phase1 → main)" -ForegroundColor White
    Write-Host "3. 创建Release (标签: v1.0.0)" -ForegroundColor White
    Write-Host "4. 查看 RELEASE_NOTES.md 获取发布说明" -ForegroundColor White
    Write-Host "5. 参考 GITHUB_RELEASE_CHECKLIST.md 完成发布" -ForegroundColor White
}

function Show-ProjectStats {
    Write-Host "`n📊 项目统计信息:" -ForegroundColor Cyan
    
    $sourceFiles = Get-ChildItem -Path "src" -Filter "*.py" | Measure-Object
    $htmlFiles = Get-ChildItem -Path "html" -Filter "*.html" -Recurse | Measure-Object
    $docFiles = Get-ChildItem -Path "." -Filter "*.md" | Measure-Object
    
    Write-Host "📁 Python源文件: $($sourceFiles.Count)" -ForegroundColor White
    Write-Host "🌐 HTML模板文件: $($htmlFiles.Count)" -ForegroundColor White
    Write-Host "📖 文档文件: $($docFiles.Count)" -ForegroundColor White
    
    $lastCommit = git log -1 --format="%h - %s"
    Write-Host "📝 最新提交: $lastCommit" -ForegroundColor White
}

# 主执行流程
Write-Host "`n开始GitHub提交检查..." -ForegroundColor Cyan

# 检查项目统计
Show-ProjectStats

# 检查Git状态
Test-GitStatus

# 测试网络连接
$connected = Test-GitHubConnection

if ($connected) {
    Write-Host "`n🎯 网络连接正常，可以尝试推送!" -ForegroundColor Green
    
    $response = Read-Host "`n是否立即推送到GitHub? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        $success = Start-GitHubPush
        if ($success) {
            Show-NextSteps
        }
    } else {
        Write-Host "✋ 推送已取消，您可以稍后手动执行: git push origin phase1" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n⏳ 网络连接不可用，请稍后重试" -ForegroundColor Yellow
    Write-Host "💡 您可以定期运行此脚本检查连接状态" -ForegroundColor Cyan
    Write-Host "📖 查看 GITHUB_SUBMIT_GUIDE.md 获取详细指导" -ForegroundColor Cyan
}

Write-Host "`n🏁 检查完成！" -ForegroundColor Green
Read-Host "按任意键退出"
