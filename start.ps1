Write-Host "配置考试系统环境..." -ForegroundColor Green
python ./scripts/setup.py

Write-Host "启动考试系统..." -ForegroundColor Green
python ./src/app.py

Write-Host "按任意键继续..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')