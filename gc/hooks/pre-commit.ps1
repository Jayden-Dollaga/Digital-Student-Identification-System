#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Host "Running Git Commander smart-commit tests before commit..." -ForegroundColor Cyan
Push-Location $scriptRoot\..\tests
try {
    pwsh -NoProfile -ExecutionPolicy Bypass -File .\test_smart_commit.ps1
    $code = $LASTEXITCODE
} catch {
    Write-Host "Error running tests: $_" -ForegroundColor Red
    $code = 1
}
Pop-Location
if ($code -ne 0) {
    Write-Host "Pre-commit checks failed. Commit aborted." -ForegroundColor Red
    Write-Host "If you believe this is a false positive, retry the commit with GC_AUTO_FIX_COMMIT=1 or run git commit --no-verify." -ForegroundColor Yellow
    exit 1
}
Write-Host "Pre-commit checks passed." -ForegroundColor Green
exit 0
