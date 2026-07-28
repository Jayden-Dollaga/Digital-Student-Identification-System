function Get-RepoInfo {
    $repoRoot = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0 -and $repoRoot) {
        $name = Split-Path -Leaf $repoRoot
    } else {
        $name = Split-Path -Leaf (Get-Location).Path
    }

    $branch = git rev-parse --abbrev-ref HEAD 2>$null
    if ($LASTEXITCODE -ne 0) { $branch = '(no branch)' }

    $status = git status --short 2>$null
    $last = git log -1 --pretty=format:"%h %s (%cr)" 2>$null
    if (-not $last) { $last = 'No commits' }

    return @{ Name=$name; Branch=$branch; Status=$status; LastCommit=$last }
}

function Show-Header {
    $info = Get-RepoInfo
    Clear-Host
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host "          Git Commander" -ForegroundColor Cyan
    Write-Host "===========================================`n" -ForegroundColor Cyan
    Write-Host "Current Project: " -NoNewline; Write-Host $info.Name -ForegroundColor Green
    Write-Host "Current Branch : " -NoNewline; Write-Host $info.Branch -ForegroundColor Green
    Write-Host "Repository Status: " -NoNewline; Write-Host ($(if ($info.Status) { 'Dirty' } else { 'Clean' })) -ForegroundColor Yellow
    Write-Host "Last Commit    : " -NoNewline; Write-Host $info.LastCommit -ForegroundColor Magenta
    Write-Host "`n-------------------------------------------`n"
}

function Show-Status {
    Show-Header
    Write-Host "Git status (short):`n" -ForegroundColor White
    git status --short | ForEach-Object { Write-Host "  $_" }
    Write-Host "`nDiff stat:`n" -ForegroundColor White
    git --no-pager diff --stat | ForEach-Object { Write-Host "  $_" }
    Write-Host "`nPress Enter to return to menu..." -ForegroundColor DarkGray
    Read-Host | Out-Null
}

function Invoke-GitCommitWithRecovery {
    param(
        [Parameter(Mandatory=$true)]
        [string]$RepoRoot,
        [Parameter(Mandatory=$true)]
        [string]$CommitMessage
    )

    Push-Location $RepoRoot
    try {
        if (Test-Path ".git/index.lock") {
            Remove-Item -Force ".git/index.lock" -ErrorAction SilentlyContinue
        }

        git add -A
        git commit -m $CommitMessage
        if ($LASTEXITCODE -eq 0) {
            return $true
        }

        return $false
    }
    finally {
        Pop-Location
    }
}

function Prompt-SmartCommit {
    $changes = git status --porcelain
    if (-not $changes) { Write-Host "No changes to commit." -ForegroundColor Yellow; return }

    # Try to use improved smart commit if available
    $suggest = $null
    if (Get-Command Get-SmartCommitMessage -ErrorAction SilentlyContinue) {
        $porc = ($changes -join "`n")
        try { $suggest = Get-SmartCommitMessage -Porcelain $porc } catch { $suggest = $null }
    }

    if (-not $suggest) {
        # fallback simple suggestion
        $first = ($changes[0].Substring(3).Trim())
        $ext = [IO.Path]::GetExtension($first).ToLower()
        $primary = switch ($ext) { '.md' {'docs'} '.py' {'feat'} default {'chore'} }
        $suggest = "${primary}: update files"
    }

    Write-Host "Suggested commit message: $suggest" -ForegroundColor Green
    $ans = Read-Host "Accept (A), Edit (E) or Cancel (C)? [A/E/C]"
    if ($ans -match '^[Aa]') {
        $ok = Invoke-GitCommitWithRecovery -RepoRoot (git rev-parse --show-toplevel 2>$null) -CommitMessage $suggest
        if ($ok) { Write-Host 'Committed.' -ForegroundColor Green } else { Write-Host 'Commit failed.' -ForegroundColor Red }
    } elseif ($ans -match '^[Ee]') {
        $msg = Read-Host "Enter commit message"
        if ($msg) {
            $ok = Invoke-GitCommitWithRecovery -RepoRoot (git rev-parse --show-toplevel 2>$null) -CommitMessage $msg
            if ($ok) { Write-Host 'Committed.' -ForegroundColor Green } else { Write-Host 'Commit failed.' -ForegroundColor Red }
        }
    } else { Write-Host 'Commit cancelled.' -ForegroundColor Yellow }
    Read-Host 'Press Enter to continue' | Out-Null
}

function Do-Push {
    $branch = git rev-parse --abbrev-ref HEAD
    Write-Host "Pushing to origin $branch..." -ForegroundColor Cyan
    git push origin $branch
    if ($LASTEXITCODE -eq 0) { Write-Host 'Push successful.' -ForegroundColor Green } else { Write-Host 'Push failed.' -ForegroundColor Red }
    Read-Host 'Press Enter to continue' | Out-Null
}

function Show-MainMenu {
    while ($true) {
        Show-Header
        Write-Host "1. Status"
        Write-Host "2. Commit (Smart)"
        Write-Host "3. Push"
        Write-Host "4. Pull"
        Write-Host "5. Exit`n"
        $c = Read-Host "Select an option"
        switch ($c) {
            '1' { Show-Status }
            '2' { Prompt-SmartCommit }
            '3' { Do-Push }
            '4' { git pull; Read-Host 'Pulled. Press Enter' | Out-Null }
            '5' { break }
            default { Write-Host 'Unknown option' -ForegroundColor Yellow }
        }
    }
}
