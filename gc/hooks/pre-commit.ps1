#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Host "Running Git Commander smart-commit tests before commit..." -ForegroundColor Cyan
Push-Location $scriptRoot\..\tests
try {
    powershell -NoProfile -ExecutionPolicy Bypass -File .\test_smart_commit.ps1
    $code = $LASTEXITCODE
} catch {
    Write-Host "Error running tests: $_" -ForegroundColor Red
    $code = 1
}
Pop-Location
if ($code -ne 0) {
    Write-Host "Pre-commit checks failed. Commit aborted." -ForegroundColor Red
    exit 1
}
Write-Host "Pre-commit checks passed." -ForegroundColor Green
exit 0
