<#
Smart commit unit-style tests.
Run from repository root:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\gc\tests\test_smart_commit.ps1
#>

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
. "$scriptRoot\..\smart_commit.ps1"

$tests = @(
    @{ name='Docs root'; porcelain = " M README.md"; expected_contains = 'docs' },
    @{ name='Code in src'; porcelain = " M src/app/main.py"; expected_contains = 'feat' },
    @{ name='Assets'; porcelain = " M assets/img/logo.png"; expected_contains = 'assets' },
    @{ name='Config yaml'; porcelain = " M config/settings.yaml"; expected_contains = 'config' },
    @{ name='Fix priority'; porcelain = " M bugfix/fix_login.py`n M bugfix/fix_logout.py`n M src/app/login.py"; expected_contains = 'fix' },
    @{ name='Multiple types'; porcelain = " M src/app/main.py`n M docs/guide.md`n M assets/icon.png"; expected_contains = 'feat' },
    @{ name='Deep folder scope'; porcelain = " M src/features/auth/login.py`n M src/features/auth/logout.py"; expected_contains = 'feat(features' },
    @{ name='Binary assets'; porcelain = " M media/sprites/sheet.png`n M media/sounds/beep.wav"; expected_contains = 'assets' },
    @{ name='Config and code'; porcelain = " M src/app/main.py`n M config/settings.yaml"; expected_contains = 'feat' },
    @{ name='Numeric prefixes'; porcelain = " M 01_init/setup.py`n M 02_init/config.yaml"; expected_contains = 'feat' },
    @{ name='Underscore scope'; porcelain = " M src/my_module/helper.py`n M src/my_module/util.py"; expected_contains = 'feat(my-module' },
    @{ name='Long filenames'; porcelain = " M src/app/very_long_filename_that_is_descriptive.py"; expected_contains = 'feat' },
    @{ name='Mixed-case paths'; porcelain = " M Src/App/Main.Py`n M DOCS/ReadMe.MD"; expected_contains = 'feat' },
    @{ name='Edge: root binary'; porcelain = " M logo.PNG"; expected_contains = 'assets' },
    @{ name='Edge: no ext'; porcelain = " M scripts/run"; expected_contains = 'chore' }
)

function Run-Test($t){
    Write-Host "Test: $($t.name)" -ForegroundColor Cyan
    $actual = Get-SmartCommitMessage -Porcelain $t.porcelain
    Write-Host "  Actual  : $actual" -ForegroundColor DarkGray
    $ok = $false
    if ($t.ContainsKey('expected')) { $ok = ($actual -eq $t.expected) }
    elseif ($t.ContainsKey('expected_contains')) { $ok = ($actual -and $actual.ToLower().Contains($t.expected_contains.ToLower())) }
    if ($ok) { Write-Host "  RESULT  : PASS`n" -ForegroundColor Green } else { Write-Host "  RESULT  : FAIL (expected contains: $($t.expected_contains))`n" -ForegroundColor Red }
    return $ok
}

$allPass = $true
foreach ($t in $tests){
    $res = Run-Test $t
    if (-not $res) { $allPass = $false }
}

if ($allPass) { Write-Host "All smart commit tests passed." -ForegroundColor Green; exit 0 } else { Write-Host "Some tests failed. Review output above." -ForegroundColor Yellow; exit 1 }
