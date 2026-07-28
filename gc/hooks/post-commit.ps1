Set-StrictMode -Version Latest
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Determine repo root
$RepoRoot = git rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0 -or -not $RepoRoot) { exit 0 }

# Get last commit hash
$commit = git rev-parse --verify HEAD 2>$null
if ($LASTEXITCODE -ne 0 -or -not $commit) { exit 0 }

$branch = git rev-parse --abbrev-ref HEAD 2>$null

try {
    Import-Module (Join-Path $ScriptRoot '..\metadata.ps1') -Force
    Update-MetadataForCommit $RepoRoot $commit $branch
    # record commit to commits.json (lines added/removed optional)
    $filesRaw = git diff-tree --no-commit-id --name-only -r $commit 2>$null
    $files = $filesRaw -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
    # basic lines added/removed via git show --stat or --numstat
    $stats = git show --numstat --format="" $commit 2>$null
    $added = 0; $removed = 0
    if ($stats) {
        $lines = $stats -split "`n"
        foreach ($l in $lines){
            $parts = $l -split "\t"
            if ($parts.Length -ge 3){
                [int]$a = 0; [int]$r = 0
                if ($parts[0] -ne '-') { [int]$a = [int]$parts[0] }
                if ($parts[1] -ne '-') { [int]$r = [int]$parts[1] }
                $added += $a; $removed += $r
            }
        }
    }
    Record-Commit $RepoRoot $commit (git log -1 --pretty=format:%B $commit) $branch $files $added $removed $null
} catch {
    # don't block commit
}
