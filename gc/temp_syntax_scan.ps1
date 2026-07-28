$ErrorActionPreference = 'Stop'
$errors = @()
Get-ChildItem -Path '.\\gc\\*.ps1' | ForEach-Object {
    $path = $_.FullName
    $tokens = @()
    $errorsRef = @()
    [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errorsRef) | Out-Null
    if ($errorsRef.Count -gt 0) {
        foreach ($e in $errorsRef) {
            $errors += [pscustomobject]@{File=$path; Line=$e.Extent.StartLineNumber; Message=$e.Message}
        }
    }
}
if ($errors.Count -gt 0) {
    $errors | Format-Table -AutoSize
    exit 1
} else {
    Write-Host 'SYNTAX_OK'
}
