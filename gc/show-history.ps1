param(
    [Parameter(Position = 0)]
    [string]$Path
)

Set-StrictMode -Version Latest
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = git rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0 -or -not $RepoRoot) {
    Write-Host 'Git repository root not found.' -ForegroundColor Red
    exit 1
}

Import-Module (Join-Path $scriptDir 'metadata.ps1') -Force

if (-not $Path) {
    $Path = Read-Host 'Enter relative path to inspect (e.g. src/app/main.py). Press Enter for repo-wide history'
}

$showRepoHistory = $false
if (-not $Path -or $Path.Trim() -eq '') {
    $showRepoHistory = $true
    $Path = $null
}

if (-not $showRepoHistory) {
    $normalized = $Path -replace '\\','/'
    $fullPath = $null
    try {
        $fullPath = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $normalized))
    } catch {
        $fullPath = $null
    }

    $relPath = $normalized
    if ($fullPath -and $fullPath.StartsWith($RepoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        $relPath = [System.IO.Path]::GetRelativePath($RepoRoot, $fullPath) -replace '\\','/'
    }
}

if ($showRepoHistory) {
    Write-Host 'Repository-wide history' -ForegroundColor Cyan
    Write-Host ('=' * 60) -ForegroundColor DarkCyan
    $commits = Load-Commits $RepoRoot
    if ($commits.Count -gt 0) {
        Write-Host 'Recent metadata-backed commits:' -ForegroundColor Green
        foreach ($c in $commits | Select-Object -Last 10) {
            Write-Host (" - {0}  {1}" -f $c.commit_hash, $c.message) -ForegroundColor DarkGray
        }
    } else {
        Write-Host '  (no metadata-backed commits found)' -ForegroundColor DarkGray
    }

    Write-Host "`nRecent Git history:" -ForegroundColor Cyan
    $gitHistory = git log --oneline -10 2>$null
    if ($LASTEXITCODE -eq 0 -and $gitHistory) {
        $gitHistory | ForEach-Object { Write-Host " - $_" -ForegroundColor DarkGray }
    } else {
        Write-Host '  (no git history found)' -ForegroundColor DarkGray
    }
    exit 0
}

$state = Load-Metadata $RepoRoot
$entry = $null
foreach ($key in $state.Keys) {
    if ($key -eq $relPath -or $key -eq $normalized) {
        $entry = $state[$key]
        break
    }
}

if (-not $entry) {
    Write-Host "No metadata found for $relPath" -ForegroundColor Yellow
    exit 0
}

Write-Host "Metadata for $relPath" -ForegroundColor Cyan
Write-Host ('=' * 60) -ForegroundColor DarkCyan
Write-Host ("SHA-256      : {0}" -f $entry.sha256) -ForegroundColor Green
Write-Host ("Last commit  : {0}" -f $entry.last_commit_hash) -ForegroundColor Green
Write-Host ("Message      : {0}" -f $entry.last_commit_message) -ForegroundColor Green
Write-Host ("Committed at : {0}" -f $entry.last_commit_timestamp) -ForegroundColor Green
Write-Host ("Modified at  : {0}" -f $entry.last_modified_utc) -ForegroundColor Green
Write-Host ("Branch       : {0}" -f $entry.last_branch) -ForegroundColor Green
Write-Host ("Category     : {0}" -f $entry.detected_category) -ForegroundColor Green
Write-Host ("Modified #   : {0}" -f $entry.modified_count) -ForegroundColor Green
Write-Host ("Status       : {0}" -f $entry.current_status) -ForegroundColor Green

$commits = Load-Commits $RepoRoot
$related = @($commits | Where-Object { $_.files -contains $relPath })
if ($related.Count -gt 0) {
    Write-Host "`nRelated commit entries:" -ForegroundColor Cyan
    foreach ($c in $related | Select-Object -Last 5) {
        Write-Host (" - {0}  {1}" -f $c.commit_hash, $c.message) -ForegroundColor DarkGray
    }
}

Write-Host "`nRecent Git history:" -ForegroundColor Cyan
$gitHistory = git log --oneline -5 -- $relPath 2>$null
if ($LASTEXITCODE -eq 0 -and $gitHistory) {
    $gitHistory | ForEach-Object { Write-Host " - $_" -ForegroundColor DarkGray }
} else {
    Write-Host '  (no git history found for this path)' -ForegroundColor DarkGray
}
