<#
Metadata module for Git Commander
Stores per-file metadata in .gitcommander/state.json under repository root.
Fields per file:
 - path (relative)
 - sha256
 - last_commit_hash
 - last_commit_message
 - last_modified_utc
 - detected_category
 - last_branch
#>

function Get-MetadataPath($RepoRoot){
    return Join-Path $RepoRoot '.gitcommander'
}

function Ensure-MetadataInitialized($RepoRoot){
    $dir = Get-MetadataPath $RepoRoot
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
    $stateFile = Join-Path $dir 'state.json'
    $commitsFile = Join-Path $dir 'commits.json'
    $historyFile = Join-Path $dir 'history.json'
    $sessionsFile = Join-Path $dir 'sessions.json'
    $cacheFile = Join-Path $dir 'cache.json'
    if (-not (Test-Path $stateFile)) { '{}' | Out-File -Encoding utf8 $stateFile }
    if (-not (Test-Path $commitsFile)) { '[]' | Out-File -Encoding utf8 $commitsFile }
    if (-not (Test-Path $historyFile)) { '[]' | Out-File -Encoding utf8 $historyFile }
    if (-not (Test-Path $sessionsFile)) { '[]' | Out-File -Encoding utf8 $sessionsFile }
    if (-not (Test-Path $cacheFile)) { '{}' | Out-File -Encoding utf8 $cacheFile }
    return @{ state=$stateFile; commits=$commitsFile; history=$historyFile; sessions=$sessionsFile; cache=$cacheFile }
}

function Load-Metadata($RepoRoot){
    $files = Ensure-MetadataInitialized $RepoRoot
    $stateFile = $files.state
    try {
        $text = Get-Content $stateFile -Raw -ErrorAction Stop
        if (-not $text) { return @{} }
        $obj = $text | ConvertFrom-Json -ErrorAction Stop
        # convert PSCustomObject to hashtable for ContainsKey/Keys semantics
        $hash = @{}
        foreach ($p in $obj.PSObject.Properties) { $hash[$p.Name] = $p.Value }
        return $hash
    } catch {
        return @{}
    }
}

function Save-Metadata($RepoRoot, $state){
    $files = Ensure-MetadataInitialized $RepoRoot
    $stateFile = $files.state
    $json = $state | ConvertTo-Json -Depth 10
    $json | Out-File -FilePath $stateFile -Encoding utf8
}

function Compute-FileHash($FullPath){
    if (-not (Test-Path $FullPath)) { return $null }
    try {
        $h = Get-FileHash -Algorithm SHA256 -Path $FullPath -ErrorAction Stop
        return $h.Hash
    } catch {
        return $null
    }
}

function Load-Commits($RepoRoot){
    $files = Ensure-MetadataInitialized $RepoRoot
    try {
        $text = Get-Content $files.commits -Raw -ErrorAction Stop
        if (-not $text -or $text.Trim() -eq '') { return @() }
        $parsed = $text | ConvertFrom-Json -ErrorAction Stop
        return @($parsed)
    } catch { return @() }
}

function Save-Commits($RepoRoot, $commits){
    $files = Ensure-MetadataInitialized $RepoRoot
    $json = $commits | ConvertTo-Json -Depth 10
    $json | Out-File -FilePath $files.commits -Encoding utf8
}

function Append-CommitEntry($RepoRoot, $entry){
    $commits = Load-Commits $RepoRoot
    $commits += $entry
    Save-Commits $RepoRoot $commits
}

function Load-Sessions($RepoRoot){
    $files = Ensure-MetadataInitialized $RepoRoot
    try {
        $text = Get-Content $files.sessions -Raw -ErrorAction Stop
        if (-not $text -or $text.Trim() -eq '') { return @() }
        $parsed = $text | ConvertFrom-Json -ErrorAction Stop
        return @($parsed)
    } catch { return @() }
}

function Save-Sessions($RepoRoot, $sessions){
    $files = Ensure-MetadataInitialized $RepoRoot
    $json = $sessions | ConvertTo-Json -Depth 10
    $json | Out-File -FilePath $files.sessions -Encoding utf8
}

function Start-Session($RepoRoot){
    $sessions = @(Load-Sessions $RepoRoot)
    $now = (Get-Date).ToUniversalTime().ToString('o')
    $session = [ordered]@{
        id = [guid]::NewGuid().ToString()
        start = $now
        end = $null
        duration_seconds = $null
        repositories = @((Split-Path $RepoRoot -Leaf))
        commands = @()
        commits = @()
        pushes = 0
        files_modified = @()
        note = $null
    }
    $sessions += $session
    Save-Sessions $RepoRoot $sessions
    return $session.id
}

function End-Session($RepoRoot, $sessionId){
    $sessions = Load-Sessions $RepoRoot
    $now = (Get-Date).ToUniversalTime()
    for ($i=0; $i -lt $sessions.Count; $i++){
        if ($sessions[$i].id -eq $sessionId){
            $start = [datetime]::Parse($sessions[$i].start)
            $sessions[$i].end = $now.ToString('o')
            $sessions[$i].duration_seconds = [int](($now - $start).TotalSeconds)
            # record files modified during session by comparing state
            $state = Load-Metadata $RepoRoot
            $modified = @()
            foreach ($k in $state.Keys){
                $entry = $state[$k]
                if ($entry.current_status -and $entry.current_status -ne 'unchanged') { $modified += $k }
            }
            $sessions[$i].files_modified = $modified
            Save-Sessions $RepoRoot $sessions
            return $true
        }
    }
    return $false
}

function Record-Commit($RepoRoot, $CommitHash, $CommitMessage, $Branch, $FilesChanged, $LinesAdded, $LinesRemoved, $SessionNote){
    $entry = [ordered]@{
        commit_hash = $CommitHash
        message = $CommitMessage
        timestamp = (Get-Date).ToUniversalTime().ToString('o')
        branch = $Branch
        repo_name = (Split-Path $RepoRoot -Leaf)
        repo_path = $RepoRoot
        files = $FilesChanged
        categories = ($FilesChanged | ForEach-Object { Get-CategoryFromPath $_ } | Sort-Object -Unique)
        lines_added = $LinesAdded
        lines_removed = $LinesRemoved
        session_note = $SessionNote
    }
    Append-CommitEntry $RepoRoot $entry
    # also attach to current open session if any
    $sessions = Load-Sessions $RepoRoot
    for ($i=$sessions.Count-1; $i -ge 0; $i--){
        if (-not $sessions[$i].end){
            $sessions[$i].commits += $CommitHash
            Save-Sessions $RepoRoot $sessions
            break
        }
    }
}

function Compare-FileHashes($RepoRoot){
    # walk repo files and compare against state.json
    $state = Load-Metadata $RepoRoot
    $changes = [ordered]@{ added=@(); modified=@(); deleted=@(); unchanged=@(); renamed=@() }
    # gather current files (tracked by git ls-files)
    $raw = git ls-files 2>$null
    $currentFiles = @()
    if ($raw) { $currentFiles = $raw -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' } }
    $stateKeys = @($state.Keys)
    # detect added and modified
    foreach ($f in $currentFiles){
        $full = Join-Path $RepoRoot $f
        $h = Compute-FileHash $full
        if ($state.ContainsKey($f)){
            $prev = $state.$f
            if ($prev.sha256 -ne $h){ $changes.modified += $f } else { $changes.unchanged += $f }
        } else {
            $changes.added += $f
        }
    }
    # detect deleted
    foreach ($k in $stateKeys){ if (-not ($currentFiles -contains $k)) { $changes.deleted += $k } }
    return $changes
}

function Get-CategoryFromPath($RelPath){
    if (-not $RelPath) { return 'unknown' }
    $p = $RelPath.ToLower()
    $ext = [IO.Path]::GetExtension($p)
    if ($ext -in @('.md','.rst','.txt')) { return 'docs' }
    if ($ext -in @('.py','.js','.ts','.java','.cs','.cpp','.c','.go','.rb')) { return 'code' }
    if ($ext -in @('.png','.jpg','.jpeg','.gif','.svg','.ico')) { return 'assets' }
    if ($ext -in @('.yml','.yaml','.json','.xml','.ini')) { return 'config' }
    if ($p -match '\btest(s)?\b' -or $p -match '(^|/)test') { return 'test' }
    if ($p -match '\bdocs?\/|\/docs?\b') { return 'docs' }
    return 'other'
}

function Update-MetadataForCommit($RepoRoot, $CommitHash, $Branch){
    if (-not $CommitHash) { return }
    $state = Load-Metadata $RepoRoot
    $files = @()
    try {
        $raw = git diff-tree --no-commit-id --name-only -r $CommitHash 2>$null
        if ($LASTEXITCODE -ne 0) { return }
        $files = $raw -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
    } catch { return }
    $commitMsg = git log -1 --pretty=format:%B $CommitHash 2>$null
    foreach ($rel in $files){
        $full = Join-Path $RepoRoot $rel
        $hash = Compute-FileHash $full
        $lastMod = $null
        if (Test-Path $full){ $lastMod = (Get-Item $full).LastWriteTimeUtc.ToString('o') }
        $category = Get-CategoryFromPath $rel
        $modifiedCount = 1
        if ($state.ContainsKey($rel) -and $state.$rel.modified_count){ $modifiedCount = [int]$state.$rel.modified_count + 1 }
        $entry = [ordered]@{
            path = $rel
            sha256 = $hash
            last_commit_hash = $CommitHash
            last_commit_message = $commitMsg
            last_commit_timestamp = (Get-Date).ToUniversalTime().ToString('o')
            last_modified_utc = $lastMod
            detected_category = $category
            last_branch = $Branch
            modified_count = $modifiedCount
            current_status = 'modified'
        }
        $state.$rel = $entry
    }
    Save-Metadata $RepoRoot $state
}

function Update-MetadataForFiles($RepoRoot, [string[]]$RelPaths, $CommitHash, $CommitMessage, $Branch){
    $state = Load-Metadata $RepoRoot
    foreach ($rel in $RelPaths){
        $full = Join-Path $RepoRoot $rel
        $hash = Compute-FileHash $full
        $lastMod = $null
        if (Test-Path $full){ $lastMod = (Get-Item $full).LastWriteTimeUtc.ToString('o') }
        $category = Get-CategoryFromPath $rel
        $modifiedCount = 1
        if ($state.ContainsKey($rel) -and $state.$rel.modified_count){ $modifiedCount = [int]$state.$rel.modified_count + 1 }
        $entry = [ordered]@{
            path = $rel
            sha256 = $hash
            last_commit_hash = $CommitHash
            last_commit_message = $CommitMessage
            last_commit_timestamp = (Get-Date).ToUniversalTime().ToString('o')
            last_modified_utc = $lastMod
            detected_category = $category
            last_branch = $Branch
            modified_count = $modifiedCount
            current_status = 'modified'
        }
        $state.$rel = $entry
    }
    Save-Metadata $RepoRoot $state
}

