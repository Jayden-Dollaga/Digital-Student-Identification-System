Set-StrictMode -Version Latest
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptRoot\checks.ps1"
. "$ScriptRoot\ui.ps1"
. "$ScriptRoot\smart_commit.ps1"
Import-Module (Join-Path $ScriptRoot 'metadata.ps1') -ErrorAction SilentlyContinue -Force

if (-not (Test-GitInstalled)) { exit 1 }

if (-not (Ensure-GitInitialized)) {
    Write-Host "Aborting: repository required." -ForegroundColor Red
    exit 1
}

Ensure-GitConfigUser
Ensure-RemoteConfigured

# repository root (git top-level)
$RepoRoot = git rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0 -or -not $RepoRoot) { $RepoRoot = (Get-Location).Path }

# Start a development session and show smart history
$SessionId = Start-Session $RepoRoot

function Show-SmartHistory(){
    $sessions = Load-Sessions $RepoRoot
    $commits = Load-Commits $RepoRoot
    if ($sessions.Count -gt 0){
        $lastSession = $sessions[-1]
    } else { $lastSession = $null }
    $lastCommit = $null
    if ($commits.Count -gt 0){ $lastCommit = $commits[-1] }

    Write-Host "Welcome back!`n" -ForegroundColor Cyan
    if ($lastCommit){
        Write-Host "Last Repository:`n  $($lastCommit.repo_name)" -ForegroundColor Green
        Write-Host "Last Commit:`n  $($lastCommit.message)`n  $($lastCommit.timestamp)" -ForegroundColor Yellow
    }
    if ($lastSession -and $lastSession.end){
        $start = [datetime]::Parse($lastSession.start)
        $end = [datetime]::Parse($lastSession.end)
        $dur = $end - $start
        Write-Host "Last session worked: $([int]$dur.TotalHours)h $([int]$dur.Minutes)m" -ForegroundColor Cyan
        if ($lastSession.note){ Write-Host "Last Session Note:`n  $($lastSession.note)" -ForegroundColor DarkGray }
    }
}

function Check-UnfinishedSession(){
    $sessions = Load-Sessions $RepoRoot
    if ($sessions.Count -eq 0) { return }
    foreach ($s in $sessions){
        if (-not $s.end -and $s.id -ne $SessionId){
            Write-Host "Previous unfinished session detected (started $($s.start))." -ForegroundColor Yellow
            if ($s.files_modified -and $s.files_modified.Count -gt 0){ Write-Host "Modified files:`n"; foreach ($f in $s.files_modified){ Write-Host "  $f" } }
            $ans = Read-Host "Resume previous work? (Y/N)"
            if ($ans -match '^[yY]') { Write-Host "Resuming previous session..." -ForegroundColor Green; return } else { End-Session $RepoRoot $s.id; Write-Host "Ignored previous session." -ForegroundColor Cyan }
        }
    }
}

function Write-Header($text){
    Write-Host ('=' * 45) -ForegroundColor DarkCyan
    Write-Host "  $text" -ForegroundColor Cyan
    Write-Host ('=' * 45) -ForegroundColor DarkCyan
}

function Pause-ForKey(){
    Write-Host "`nPress Enter to continue..." -NoNewline
    [void][System.Console]::ReadLine()
}

function Test-Git(){
    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git){
        Write-Host "Git is not installed or not in PATH." -ForegroundColor Red
        Write-Host "Install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
        return $false
    }
    return $true
}

function Is-GitRepo(){
    $p = git rev-parse --is-inside-work-tree 2>$null
    return $LASTEXITCODE -eq 0
}

function Ensure-RepoInitialized(){
    if (-not (Is-GitRepo)){
        Write-Host "This folder is not a Git repository." -ForegroundColor Yellow
        $ans = Read-Host "Initialize a new Git repository here? (y/n)"
        if ($ans -match '^[yY]'){
            git init
            if ($LASTEXITCODE -ne 0){ Write-Host "git init failed." -ForegroundColor Red; Pause-ForKey; exit }
            Write-Host "Repository initialized." -ForegroundColor Green
        } else { Write-Host "Repository required. Exiting." -ForegroundColor Red; Pause-ForKey; exit }
    }
}

function Ensure-GitConfig(){
    $name = git config --get user.name
    $email = git config --get user.email
    if (-not $name){
        $n = Read-Host "Git user.name not set. Enter your name"
        if ($n) { git config user.name "${n}" }
    }
    if (-not $email){
        $e = Read-Host "Git user.email not set. Enter your email"
        if ($e) { git config user.email "${e}" }
    }
}

function Ensure-Remote(){
    $remotes = git remote -v 2>$null
    if (-not $remotes){
        Write-Host "No Git remote configured." -ForegroundColor Yellow
        $url = Read-Host "Add remote URL (or leave empty to skip)"
        if ($url){ git remote add origin $url }
    }
}

function Show-Status(){
    Write-Header "Repository Status"
    git rev-parse --abbrev-ref HEAD 2>$null | ForEach-Object { Write-Host "Current Branch: " $_ -ForegroundColor Green }
    Write-Host "`nGit status (short):`n" -ForegroundColor Cyan
    git status --short
    Write-Host "`nLast commit:`n" -ForegroundColor Cyan
    git --no-pager log -1 --pretty=format:"%h %ad %s" --date=short
    Pause-ForKey
}

function Do-SmartCommit(){
    $changes = git status --porcelain
    if (-not $changes){ Write-Host "No changes to commit." -ForegroundColor Green; Pause-ForKey; return }
    $suggest = Get-SmartCommitMessage -Porcelain $changes
    Write-Host "Suggested commit message:`n" -ForegroundColor Cyan
    Write-Host $suggest -ForegroundColor Yellow
    $choice = Read-Host "(A)ccept, (E)dit, (C)ancel"
    $committed = $false
    switch ($choice.ToUpper()){
        'A' {
            git add -A
            git commit -m "$suggest"
            if ($LASTEXITCODE -eq 0){ Write-Host "Committed." -ForegroundColor Green; $committed = $true } else { Write-Host "Commit failed." -ForegroundColor Red }
        }
        'E' {
            $tmp = [IO.Path]::GetTempFileName()
            Set-Content -Path $tmp -Value $suggest -Encoding UTF8
            notepad $tmp
            $new = Get-Content $tmp -Raw
            if ($new.Trim()){
                git add -A
                git commit -m $new
                if ($LASTEXITCODE -eq 0){ Write-Host "Committed." -ForegroundColor Green; $committed = $true } else { Write-Host "Commit failed." -ForegroundColor Red }
            } else { Write-Host "Empty message, aborting." -ForegroundColor Yellow }
            Remove-Item $tmp -Force
        }
        default { Write-Host "Cancelled." -ForegroundColor Yellow }
    }

    # If we committed, update the metadata store with files in the new commit
    if ($committed){
        try {
            $commitHash = git rev-parse --verify HEAD 2>$null
            if ($LASTEXITCODE -eq 0 -and $commitHash){
                $branch = git rev-parse --abbrev-ref HEAD 2>$null
                $filesRaw = git diff-tree --no-commit-id --name-only -r $commitHash 2>$null
                $files = $filesRaw -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
                $commitMsg = git log -1 --pretty=format:%B $commitHash 2>$null
                Import-Module (Join-Path $ScriptRoot 'metadata.ps1') -Force
                Update-MetadataForFiles $RepoRoot $files $commitHash $commitMsg $branch
            }
        } catch {
            Write-Host "Metadata update failed: $_" -ForegroundColor Yellow
        }
    }
    Pause-ForKey
}

function Do-Push(){
    $status = git status --porcelain
    if ($status){
        $ans = Read-Host "Uncommitted changes exist. Commit before push? (y/n)"
        if ($ans -match '^[yY]'){ Do-SmartCommit } else { Write-Host "Push aborted due to uncommitted changes." -ForegroundColor Yellow; Pause-ForKey; return }
    }
    Write-Host "Pushing to remote..." -ForegroundColor Cyan
    git push origin --all
    if ($LASTEXITCODE -eq 0){ Write-Host "Push successful." -ForegroundColor Green } else { Write-Host "Push failed." -ForegroundColor Red }
    Pause-ForKey
}

function Do-Pull(){
    Write-Host "Pulling from remote..." -ForegroundColor Cyan
    git pull
    if ($LASTEXITCODE -eq 0){ Write-Host "Pull successful." -ForegroundColor Green } else { Write-Host "Pull failed." -ForegroundColor Red }
    Pause-ForKey
}

function Do-Backup(){
    $project = Split-Path -Leaf $RepoRoot
    $ts = Get-Date -Format "yyyy-MM-dd_HHmm"
    $backupsDir = Join-Path $RepoRoot 'Backups'
    New-Item -ItemType Directory -Force -Path $backupsDir | Out-Null
    $out = Join-Path $backupsDir ("${project}_$ts.zip")
    Write-Host "Creating backup $out" -ForegroundColor Cyan
    Push-Location $RepoRoot
    try {
        if (Test-Path $out) {
            Remove-Item $out -Force -ErrorAction SilentlyContinue
        }

        $sourceItems = Get-ChildItem -LiteralPath $RepoRoot -Force | Where-Object {
            $_.FullName -ne $out -and $_.Name -ne 'Backups'
        }

        if ($sourceItems.Count -eq 0) {
            Write-Host "Backup failed: no source items found." -ForegroundColor Red
        } else {
            Compress-Archive -Path $sourceItems.FullName -DestinationPath $out -Force -ErrorAction Stop
            if (Test-Path $out -and (Get-Item $out).Length -gt 0) {
                Write-Host "Backup created: $out" -ForegroundColor Green
            } else {
                Write-Host "Backup failed." -ForegroundColor Red
            }
        }
    } catch {
        Write-Host "Backup error: $($_.Exception.Message)" -ForegroundColor Red
    } finally {
        Pop-Location
    }
    Pause-ForKey
}

function Do-Release(){
    $ver = Read-Host "Enter version (e.g. 1.2.3)"
    if (-not $ver){ Write-Host "Aborted." -ForegroundColor Yellow; return }
    if ($ver -notmatch '^[0-9]+\.[0-9]+\.[0-9]+$'){
        $ok = Read-Host "Version doesn't match X.Y.Z. Continue anyway? (y/N)"
        if ($ok -notmatch '^[yY]'){ Write-Host 'Aborted.' -ForegroundColor Yellow; Pause-ForKey; return }
    }
    $tagName = "v$ver"
    # check existing tag
    $exists = git rev-parse -q --verify "refs/tags/$tagName" 2>$null
    if ($LASTEXITCODE -eq 0){
        $ov = Read-Host "Tag $tagName already exists. Overwrite? (y/N)"
        if ($ov -notmatch '^[yY]'){ Write-Host 'Aborted.' -ForegroundColor Yellow; Pause-ForKey; return }
        git tag -d $tagName
    }
    git tag -a $tagName -m "Release $tagName"
    if ($LASTEXITCODE -ne 0){ Write-Host "Tag creation failed." -ForegroundColor Red; Pause-ForKey; return }
    Write-Host "Pushing tag $tagName to origin..." -ForegroundColor Cyan
    git push origin $tagName
    if ($LASTEXITCODE -eq 0){ Write-Host "Release pushed." -ForegroundColor Green } else { Write-Host "Push tag failed." -ForegroundColor Red }
    Pause-ForKey
}

function Show-RepoInfo(){
    Write-Header "Repository Info"
    $name = git rev-parse --show-toplevel 2>$null | Split-Path -Leaf
    Write-Host "Repository: " $name -ForegroundColor Cyan
    $remote = git remote get-url origin 2>$null
    $remoteDisplay = if ($remote) { $remote } else { '(none)' }
    Write-Host "Remote: " $remoteDisplay -ForegroundColor Cyan
    $branch = git rev-parse --abbrev-ref HEAD 2>$null
    Write-Host "Branch: " $branch -ForegroundColor Cyan
    $commits = git rev-list --all --count 2>$null
    Write-Host "Total commits: " $commits -ForegroundColor Cyan
    $latestTag = git describe --tags --abbrev=0 2>$null
    $latestTagDisplay = if ($latestTag) { $latestTag } else { '(none)' }
    Write-Host "Latest tag: " $latestTagDisplay -ForegroundColor Cyan
    Pause-ForKey
}

function Show-HistoryInspector(){
    $path = Read-Host "Enter relative path to inspect (e.g. src/app/main.py)"
    if (-not $path) { Write-Host "Cancelled." -ForegroundColor Yellow; Pause-ForKey; return }
    & (Join-Path $ScriptRoot 'show-history.ps1') -Path $path
    Pause-ForKey
}

function Main-Menu(){
    while ($true){
        Clear-Host
        Write-Header "Git Commander"
        $branch = git rev-parse --abbrev-ref HEAD 2>$null
        $status = git status --short
        $remote = git remote get-url origin 2>$null
        $last = git --no-pager log -1 --pretty=format:"%h %ad %s" --date=short 2>$null
        $projectName = Split-Path -Leaf $RepoRoot
        Write-Host "Project: " $projectName -ForegroundColor Green
        Write-Host "Branch : " $branch -ForegroundColor Green
        $remoteDisplay = if ($remote) { $remote } else { '(none)' }
        $lastDisplay = if ($last) { $last } else { '(none)' }
        Write-Host "Remote : " $remoteDisplay -ForegroundColor Green
        Write-Host "Last   : " $lastDisplay -ForegroundColor Green
        Write-Host "`nMenu:`n1) Status    2) Commit    3) Push    4) Pull`n5) Release   6) Backup    7) Repo Info   8) Show History   9) Exit`n"
        $sel = Read-Host "Choose an option (1-9)"
        switch ($sel){
            '1' { Show-Status }
            '2' { Do-SmartCommit }
            '3' { Do-Push }
            '4' { Do-Pull }
            '5' { Do-Release }
            '6' { Do-Backup }
            '7' { Show-RepoInfo }
            '8' { Show-HistoryInspector }
            '9' { break }
            default { Write-Host "Invalid choice." -ForegroundColor Yellow; Pause-ForKey }
        }
    }
}

# Entry
if (-not (Test-Git)) { Pause-ForKey; exit }
Ensure-RepoInitialized
Ensure-GitConfig
Ensure-Remote
Show-SmartHistory
Check-UnfinishedSession
try {
    Main-Menu
} finally {
    End-Session $RepoRoot $SessionId | Out-Null
}
