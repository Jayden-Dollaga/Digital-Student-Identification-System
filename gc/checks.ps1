function Test-GitInstalled {
    $git = & git --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Git is not installed or not in PATH." -ForegroundColor Red
        Write-Host "Install Git from https://git-scm.com/download/win and rerun." -ForegroundColor Yellow
        return $false
    }
    return $true
}

function Test-IsGitRepo {
    $res = & git rev-parse --is-inside-work-tree 2>$null
    return $LASTEXITCODE -eq 0
}

function Ensure-GitInitialized {
    if (-not (Test-IsGitRepo)) {
        $ans = Read-Host "This folder is not a Git repository. Initialize here? (y/N)"
        if ($ans -match '^[Yy]') {
            git init
            if ($LASTEXITCODE -ne 0) { Write-Host "git init failed" -ForegroundColor Red; exit 1 }
            Write-Host "Repository initialized." -ForegroundColor Green
            return $true
        }
        return $false
    }
    return $true
}

function Ensure-GitConfigUser {
    $name = git config user.name
    $email = git config user.email
    if (-not $name) {
        $n = Read-Host "Git user.name is not set. Set it now (your name) or leave blank"
        if ($n) { git config user.name "$n" }
    }
    if (-not $email) {
        $e = Read-Host "Git user.email is not set. Set it now (you@example.com) or leave blank"
        if ($e) { git config user.email "$e" }
    }
}

function Ensure-RemoteConfigured {
    $url = git remote get-url origin 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $url) {
        Write-Host "No remote named 'origin' found." -ForegroundColor Yellow
        $add = Read-Host "Add a remote URL now? (e.g. https://github.com/user/repo.git) Leave blank to skip"
        if ($add) { git remote add origin $add; if ($LASTEXITCODE -eq 0) { Write-Host 'Remote added.' -ForegroundColor Green } }
    }
}
