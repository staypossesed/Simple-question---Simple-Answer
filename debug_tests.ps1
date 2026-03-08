# Debug script — 10 тестов (PowerShell, без Python)
# Запуск: .\debug_tests.ps1

$passed = 0
$total = 10

function Test-Check {
    param($Name, $Ok, $Detail = "")
    $status = if ($Ok) { "✅ PASS" } else { "❌ FAIL" }
    Write-Host "$status | $Name"
    if ($Detail) { Write-Host "       -> $Detail" }
    if ($Ok) { $script:passed++ }
}

Write-Host ""
Write-Host "=== RAG App Debug - 10 tests ==="
Write-Host ""

# 1. Python
$py = Get-Command python -ErrorAction SilentlyContinue
$pyOk = $null -ne $py
try {
    $v = & python --version 2>&1
    if ($v -match "was not found|Microsoft Store") { $pyOk = $false }
} catch { $pyOk = $false }
Test-Check "1. Python installed" $pyOk "Install from python.org or Microsoft Store"

# 2. Working dir
$cwd = Get-Location
$dirOk = $cwd.Path -match "portfolio-rag-app"
Test-Check "2. In portfolio-rag-app" $dirOk "CWD: $($cwd.Path)"

# 3. .env exists
$envPath = Join-Path $cwd ".env"
$envOk = Test-Path $envPath
Test-Check "3. .env exists" $envOk $envPath

# 4. OPENAI_API_KEY
$key = ""
if ($envOk) {
    $content = Get-Content $envPath -Raw
    if ($content -match 'OPENAI_API_KEY=(.+)') {
        $key = $matches[1].Trim().Trim('"').Trim("'")
    }
}
$keyOk = $key.Length -gt 20 -and $key.StartsWith("sk-") -and $key -ne "sk-your-key-here"
Test-Check "4. OPENAI_API_KEY valid" $keyOk "Length: $($key.Length)"

# 5. app.yaml
$yamlOk = Test-Path (Join-Path $cwd "app.yaml")
Test-Check "5. app.yaml exists" $yamlOk

# 6. data/
$dataOk = Test-Path (Join-Path $cwd "data")
$files = if ($dataOk) { (Get-ChildItem (Join-Path $cwd "data") -File).Count } else { 0 }
Test-Check "6. data/ folder" $dataOk "Files: $files"

# 7. Docker
$docker = Get-Command docker -ErrorAction SilentlyContinue
$dockerOk = $null -ne $docker
Test-Check "7. Docker installed" $dockerOk "Required for Windows if Python fails"

# 8. app.py
$appOk = Test-Path (Join-Path $cwd "app.py")
Test-Check "8. app.py exists" $appOk

# 9. requirements.txt
$reqOk = Test-Path (Join-Path $cwd "requirements.txt")
Test-Check "9. requirements.txt exists" $reqOk

# 10. ui/
$uiOk = Test-Path (Join-Path $cwd "ui\ui.py")
Test-Check "10. ui/ui.py exists" $uiOk

Write-Host "`n=========================================="
Write-Host "RESULT: $passed/10 tests passed`n"

if (-not $pyOk) {
    Write-Host "⚠ Python not found. Install: https://www.python.org/downloads/" -ForegroundColor Yellow
}
if (-not $dockerOk) {
    Write-Host "⚠ Docker not found. Install: https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe" -ForegroundColor Yellow
}
if ($pyOk -and $keyOk -and $passed -ge 8) {
    Write-Host "Try: pip install -r requirements.txt; python app.py" -ForegroundColor Green
}
if ($dockerOk -and $keyOk -and $passed -ge 8) {
    Write-Host "Or: docker compose up" -ForegroundColor Green
}
