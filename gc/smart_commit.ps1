function Get-SmartCommitMessage {
    param(
        [string]$Porcelain
    )

    if (-not $Porcelain) { $Porcelain = git status --porcelain }
    $lines = $Porcelain -split "`n" | Where-Object { $_ -and $_.Trim() }
    if (-not $lines) { return $null }

    $types = @{}
    $scopes = @{}
    # load metadata (optional)
    $RepoRootLocal = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $RepoRootLocal) { $RepoRootLocal = (Get-Location).Path }
    $prevTypes = @{}
    $prevSubjects = @()
    try {
        $metaPath = Join-Path $RepoRootLocal 'gc\metadata.ps1'
        if (Test-Path $metaPath) { Import-Module $metaPath -ErrorAction SilentlyContinue -Force; $meta = Load-Metadata $RepoRootLocal } else { $meta = $null }
    } catch { $meta = $null }
    foreach ($line in $lines) {
        # porcelain format: XY <path>
        $path = $line
        if ($path.Length -gt 3) { $path = $path.Substring(3) }
        $path = $path.Trim() -replace "\\","/"
        $ext = [IO.Path]::GetExtension($path).ToLower()
        $fileName = [IO.Path]::GetFileName($path)
        $fileBaseName = [IO.Path]::GetFileNameWithoutExtension($path)
        $lower = $path.ToLower()

        # determine scope from the first meaningful directory segment after any generic top-level container
        $candidate = $null
        $segments = $lower -split '/'
        $segments = $segments | Where-Object { $_ -and $_ -ne '.' }

        if ($segments.Count -gt 1) {
            $dirSegments = @($segments[0..($segments.Count - 2)])
            foreach ($segment in $dirSegments) {
                if (-not $segment) { continue }
                $segment = [IO.Path]::GetFileNameWithoutExtension($segment)
                $segment = $segment -replace '^[0-9]+[_-]?', ''
                if ($segment -match '^(src|lib|bin|dist|assets|docs|doc|test|tests|data|config|backup|organized|gc|git|root|main|app|index|package|module|utils|helpers)$') {
                    continue
                }
                if ($segment -and $segment.Length -gt 1) {
                    $candidate = $segment
                    break
                }
            }
        }

        if (-not $candidate) {
            $candidate = $fileBaseName
            if (-not $candidate) { $candidate = $fileName }
        }

        # normalize scope: remove numeric prefixes and sanitize, keep only clean slug text
        $scope = $candidate -replace '^[0-9]+[_-]?', '' -replace '\.[a-z0-9]+$','' -replace '[^a-z0-9_-]', '-' -replace '_','-' -replace '--+','-'
        $scope = $scope.Trim('-')
        if ($scope) { $scopes[$scope] = ($scopes[$scope] + 1) }

        # type heuristics
        if ($lower -match '\bdoc(s)?\b' -or $ext -in @('.md','.rst')) { $types['docs'] = ($types['docs'] + 1) }
        elseif ($lower -match '\btest(s)?\b' -or $path -match '(?i)test') { $types['test'] = ($types['test'] + 1) }
        elseif ($ext -in @('.png','.jpg','.jpeg','.gif','.svg','.ico')) { $types['assets'] = ($types['assets'] + 1) }
        elseif ($ext -in @('.yml','.yaml','.json','.xml')) { $types['config'] = ($types['config'] + 1) }
        elseif ($lower -match '(?<![a-z])(?:fix|bug)(?![a-z])' -or $lower -match '(?<![a-z])(?:fix|bug)[-_]' -or $lower -match '(?:^|[\/._-])(fix|bug)(?:[\/._-]|$)') { $types['fix'] = ($types['fix'] + 1) }
        elseif ($ext -in @('.ps1','.py','.js','.ts','.java','.cs','.cpp','.c','.go','.rb')) { $types['feat'] = ($types['feat'] + 1) }
        else { $types['chore'] = ($types['chore'] + 1) }

        # inspect metadata for this file to detect previous commit intent
        if ($meta) {
            $key = $path
            $entry = $null
            try { $entry = $meta."$key" } catch { $entry = $null }
            if (-not $entry) {
                # try normalized path separator
                $alt = $path -replace '/','\\'
                try { $entry = $meta."$alt" } catch { $entry = $null }
            }
            if ($entry -and $entry.last_commit_message) {
                if ($entry.last_commit_message -match '^(?<t>\w+)(\((?<s>[^)]+)\))?:\s*(?<sub>.+)$'){
                    $pt = $Matches['t'].ToLower()
                    $psub = $Matches['sub']
                    $prevTypes[$pt] = ($prevTypes[$pt] + 1)
                    $prevSubjects += $psub
                }
            }
        }
    }

    # choose dominant type by highest count, with priority ordering
    $priority = @('fix','feat','docs','test','perf','refactor','style','config','assets','chore')
    $chosenType = $null
    # incorporate previous commit types to bias suggestions
    if ($prevTypes.Count -gt 0){
        foreach ($k in $prevTypes.Keys){
            switch ($k) {
                'feat' { $types['refactor'] = ($types['refactor'] + $prevTypes[$k]) }
                default { $types[$k] = ($types[$k] + $prevTypes[$k]) }
            }
        }
    }
    foreach ($p in $priority) {
        if ($types.ContainsKey($p)) { $chosenType = $p; break }
    }
    if (-not $chosenType -and $types.Count -gt 0) { $chosenType = ($types.GetEnumerator() | Sort-Object -Property Value -Descending | Select-Object -First 1).Name }

    # choose scope - most common (sanitize)
    $chosenScope = $null
    if ($scopes.Count -gt 0) { $chosenScope = ($scopes.GetEnumerator() | Sort-Object -Property Value -Descending | Select-Object -First 1).Name }
    if ($chosenScope -and $chosenScope -match '^(\.|git|organized|backups|node_modules)$') { $chosenScope = $null }

    # create a short actionable summary
    switch ($chosenType) {
        'feat'     { $summaryVerb = 'add or update' }
        'fix'      { $summaryVerb = 'fix' }
        'docs'     { $summaryVerb = 'update docs for' }
        'test'     { $summaryVerb = 'add tests for' }
        'config'   { $summaryVerb = 'update config for' }
        'assets'   { $summaryVerb = 'update assets for' }
        'refactor' { $summaryVerb = 'continue' }
        default    { $summaryVerb = 'maintenance for' }
    }

    if ($chosenScope) {
        if ($summaryVerb -eq 'continue' -and $prevSubjects.Count -gt 0) {
            # continue previous subject if available
            $prev = $prevSubjects | Where-Object { $_ } | Select-Object -First 1
            if ($prev) { $summary = "$summaryVerb $prev" } else { $summary = "$summaryVerb $chosenScope" }
        } else {
            $summary = "$summaryVerb $chosenScope"
        }
        $scopePart = "($chosenScope)"
    } else {
        # if no scope, pick representative filename(s) without extension
        $sample = [IO.Path]::GetFileNameWithoutExtension($lines[0] -replace '^.\s+','')
        if ($summaryVerb -eq 'continue' -and $prevSubjects.Count -gt 0) {
            $prev = $prevSubjects | Where-Object { $_ } | Select-Object -First 1
            if ($prev) { $summary = "$summaryVerb $prev" } else { $summary = "$summaryVerb $sample" }
        } else {
            $summary = "$summaryVerb $sample"
        }
        $scopePart = ''
    }

    # grammar / summary post-processing
    function Normalize-Summary($text){
        if (-not $text) { return $text }
        $t = $text.Trim()
        # remove trailing punctuation
        $t = $t.TrimEnd('.', ' ')
        # collapse multiple spaces
        $t = ($t -split '\s+') -join ' '
        # remove duplicate adjacent words: 'update update' -> 'update'
        $t = [regex]::Replace($t, '\b(\w+)\s+\1\b', '$1', 'IgnoreCase')
        # normalize some common phrases
        $t = $t -replace '(?i)add or update', 'add/update'
        $t = $t -replace '(?i)update configuration for', 'update config for'
        $t = $t -replace '(?i)update configuration', 'update config'
        $t = $t -replace '(?i)update docs for', 'update docs'
        $t = $t -replace '(?i)add tests for', 'add tests'
        $t = $t -replace '(?i)maintenance for', 'maintenance'
        $t = $t -replace '(?i)update assets for', 'update assets'
        $t = $t -replace '(?i)fix bugfix', 'fix'
        $t = $t -replace '\s+for\s+repo$', ''
        # lower-case first char
        if ($t.Length -gt 0) { $t = $t.Substring(0,1).ToLower() + $t.Substring(1) }
        # limit summary to 72 chars
        if ($t.Length -gt 72) { $t = $t.Substring(0,69) + '...' }
        return $t
    }

    $summary = Normalize-Summary $summary

    # build conventional commit: type(scope): summary
    $ccType = switch ($chosenType) {
        'feat' { 'feat' }
        'fix'  { 'fix' }
        'docs' { 'docs' }
        'test' { 'test' }
        'config' { 'chore' }
        'assets' { 'chore' }
        default { 'chore' }
    }

    $message = "${ccType}${scopePart}: ${summary}"

    return $message
}

try { export-modulemember -function * } catch { }
