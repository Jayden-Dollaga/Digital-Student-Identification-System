$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
. "$scriptRoot\..\ui.ps1"

$tempDir = Join-Path $env:TEMP ("gc-commit-lock-" + [System.Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
Push-Location $tempDir
try {
    git init | Out-Null
    git config user.name 'Test User'
    git config user.email 'test@example.com'

    Set-Content -Path (Join-Path $tempDir 'sample.txt') -Value 'hello'
    New-Item -Path (Join-Path $tempDir '.git/index.lock') -ItemType File -Force | Out-Null

    $ok = Invoke-GitCommitWithRecovery -RepoRoot $tempDir -CommitMessage 'test: add sample'
    if (-not $ok) {
        throw 'Commit helper returned false'
    }

    $commit = git log -1 --pretty=format:%s
    if ($commit -ne 'test: add sample') {
        throw "Unexpected commit message: $commit"
    }

    Write-Host 'Commit lock recovery test passed.' -ForegroundColor Green
    exit 0
}
catch {
    Write-Host "Commit lock recovery test failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
finally {
    Pop-Location
    if (Test-Path $tempDir) {
        Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
