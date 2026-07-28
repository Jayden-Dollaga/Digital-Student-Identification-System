# Git Commander (portable)

Run `GitCommander.bat` in a Windows project folder to launch an interactive Git helper.

Features implemented:

- First-run checks: Git installed, repo init, user.name/email, remote 'origin'
- Interactive main menu: Status, Smart Commit, Push, Pull, Release, Backup, Repo Info, Show History, Exit
- Persistent metadata store for file history and smarter commit suggestions
- Pre-commit and post-commit hook installation for validation and metadata updates
- History inspection for recorded file metadata

Completed checklist:

- [x] Backup workflow
- [x] Release workflow
- [x] History inspection
- [x] Hook installation and metadata tracking
- [x] Smart commit heuristics and tests

Hooks:

- To install the pre-commit checks (runs smart-commit tests before commits), run `gc\install_hooks.bat` from the repo root.
  This writes a `.git/hooks/pre-commit` wrapper that invokes the PowerShell hook `gc\hooks\pre-commit.ps1`.

Tests:

- Smart commit unit tests are located at `gc\tests\test_smart_commit.ps1`. Run them with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\gc\tests\test_smart_commit.ps1
```

If the tests fail, the pre-commit hook will abort the commit.

CI:

- A GitHub Actions workflow is included at `.github/workflows/git-commander-tests.yml`.
- Two workflows are included:
  - `.github/workflows/git-commander-tests.yml` — runs smart-commit tests on `windows-latest` (legacy).
  - `.github/workflows/git-commander-ci-matrix.yml` — CI matrix that runs the smart-commit tests on `windows-latest`, `ubuntu-latest`, and `macos-latest` for pushes and pull requests to `main`.

Metadata:

- Git Commander maintains a hidden metadata store at `.gitcommander/state.json` (created automatically).
- For every tracked file, Git Commander records the relative path, SHA-256, last commit hash, last commit message, last modified timestamp (UTC), detected category, and last branch.
- A `post-commit` hook is installed by `gc\install_hooks.bat` (or can be installed manually) to update this metadata after every successful commit.
- The metadata is used to improve Smart Commit suggestions (for example, suggesting `refactor(scope): continue ...` when continuing work started by a `feat(scope): ...` commit).

Optional future enhancements: richer analytics dashboards and config-driven tuning.
