import ast
import csv
import io
import os
import re
import subprocess
import sys
import tokenize
from pathlib import Path

root = Path(r'c:/Users/EnforcerX/Downloads/Arduino-IDE - Project/AI-Assisted Fingerprint Attendance System').resolve()
exclude_dirs = {'.git', '.svn', '.hg', '.venv', '.venv-1', '__pycache__', '.pytest_cache', '.mypy_cache', '.vscode', 'build', 'dist', 'node_modules', 'site-packages', 'venv', 'env'}
source_exts = {'.py', '.pyw', '.cpp', '.cc', '.cxx', '.c', '.h', '.hpp', '.hh', '.ino', '.pde', '.js', '.ts', '.jsx', '.tsx', '.sh', '.bash', '.zsh', '.bat', '.cmd', '.ps1', '.m', '.swift', '.java', '.kt', '.rb', '.go', '.rs', '.php', '.lua', '.sql', '.pl', '.r', '.sas', '.cs', '.vb', '.f90', '.f95', '.f03', '.for', '.f', '.asm', '.s', '.S'}


def classify_language(path: Path):
    ext = path.suffix.lower()
    if ext in {'.py', '.pyw'}:
        return 'Python'
    if ext in {'.ino', '.pde', '.cpp', '.cc', '.cxx', '.hpp', '.hh', '.h'}:
        return 'Arduino/C++'
    if ext == '.c':
        return 'C'
    if ext in {'.js', '.jsx', '.ts', '.tsx'}:
        return 'JavaScript'
    if ext in {'.sh', '.bash', '.zsh', '.ps1', '.bat', '.cmd'}:
        return 'Shell'
    return 'Other'


def classify_component(path: Path):
    parts = [p.lower() for p in path.parts]
    if 'firmware' in parts:
        return 'ESP32 Firmware'
    if 'tests' in parts:
        return 'Tests'
    if 'tools' in parts or path.name in {'run_app.bat', 'run_qt_gui.bat', 'run_qt_gui.py', 'install_requirements.bat', 'list_files.bat'}:
        return 'Tools/Scripts'
    if 'gui_qt' in parts or 'qt' in parts:
        return 'Qt GUI'
    if 'gui' in parts or 'legacy-ui' in parts or 'legacy' in parts or 'archive' in parts or 'experimental' in parts or 'delete' in parts:
        return 'Legacy GUI'
    if 'python' in parts:
        return 'Python Backend'
    return 'Other'


def classify_category(path: Path):
    parts = [p.lower() for p in path.parts]
    if any(p in {'archive', 'archived', 'legacy', 'legacy-ui', 'experimental', 'delete', 'backups', 'backup'} for p in parts):
        return 'legacy/archived'
    if 'generated' in parts:
        return 'generated'
    if any(token in str(path).lower() for token in ['copy', 'copyof', 'bak', 'orig', 'old', 'tmp', 'save']):
        return 'legacy/duplicate'
    return 'active'


def count_lines(path: Path, language: str):
    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        text = path.read_text(encoding='latin-1', errors='ignore')
    lines = text.splitlines()
    physical = len(lines)
    blank = 0
    comment = 0
    code = 0

    if language == 'Python':
        try:
            tree = ast.parse(text)
        except Exception:
            tree = None
        docstring_lines = set()
        if tree is not None:
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                    doc = ast.get_docstring(node)
                    if doc is not None:
                        start = getattr(node, 'lineno', 0)
                        end = getattr(node, 'end_lineno', start)
                        for ln in range(start, end + 1):
                            docstring_lines.add(ln)
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
        except Exception:
            tokens = []
        line_to_tokens = {}
        for tok in tokens:
            line_to_tokens.setdefault(tok.start[0], []).append(tok)
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                blank += 1
                continue
            if idx in docstring_lines:
                comment += 1
                continue
            has_code = False
            for tok in line_to_tokens.get(idx, []):
                if tok.type in {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER}:
                    continue
                if tok.type == tokenize.STRING:
                    continue
                has_code = True
                break
            if has_code:
                code += 1
            else:
                comment += 1
    elif language in {'Arduino/C++', 'C'}:
        in_block = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank += 1
                continue
            if in_block:
                comment += 1
                if '*/' in line:
                    in_block = False
                continue
            if '/*' in line and '*/' in line:
                comment += 1
                continue
            if '/*' in line:
                if line.split('/*', 1)[0].strip():
                    code += 1
                else:
                    comment += 1
                in_block = True
                continue
            if '//' in line:
                if line.split('//', 1)[0].strip():
                    code += 1
                else:
                    comment += 1
            else:
                code += 1
    else:
        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank += 1
                continue
            if language == 'Shell':
                if stripped.startswith('#') or stripped.lower().startswith('rem') or stripped.startswith('::'):
                    comment += 1
                else:
                    code += 1
            else:
                if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*') or stripped.startswith('#'):
                    comment += 1
                else:
                    code += 1
    return {'physical_lines': physical, 'blank_lines': blank, 'comment_lines': comment, 'code_lines': code}


rows = []
metrics = {}
for path in sorted(root.rglob('*')):
    if not path.is_file():
        continue
    if any(part in exclude_dirs for part in path.parts):
        continue
    if path.suffix.lower() not in source_exts:
        continue
    try:
        path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        continue
    language = classify_language(path)
    stat = count_lines(path, language)
    category = classify_category(path)
    component = classify_component(path)
    rel = path.relative_to(root).as_posix()
    rows.append({
        'path': rel,
        'language': language,
        'extension': path.suffix.lower(),
        'physical_lines': stat['physical_lines'],
        'blank_lines': stat['blank_lines'],
        'comment_lines': stat['comment_lines'],
        'code_lines': stat['code_lines'],
        'category': category,
        'component': component,
    })
    metrics.setdefault(component, {'files': 0, 'physical': 0, 'code': 0})
    metrics[component]['files'] += 1
    metrics[component]['physical'] += stat['physical_lines']
    metrics[component]['code'] += stat['code_lines']

out_dir = root / 'audit'
out_dir.mkdir(exist_ok=True)
with (out_dir / 'source_line_counts.csv').open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['path', 'language', 'extension', 'physical_lines', 'blank_lines', 'comment_lines', 'code_lines', 'category'])
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row[k] for k in ['path', 'language', 'extension', 'physical_lines', 'blank_lines', 'comment_lines', 'code_lines', 'category']})

docs_dir = root / 'docs'
docs_dir.mkdir(exist_ok=True)
with (docs_dir / 'CODE_METRICS.csv').open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['path', 'language', 'extension', 'physical_lines', 'blank_lines', 'comment_lines', 'code_lines', 'category'])
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row[k] for k in ['path', 'language', 'extension', 'physical_lines', 'blank_lines', 'comment_lines', 'code_lines', 'category']})

lang_totals = {}
for row in rows:
    d = lang_totals.setdefault(row['language'], {'files': 0, 'physical': 0, 'blank': 0, 'comment': 0, 'code': 0})
    d['files'] += 1
    d['physical'] += row['physical_lines']
    d['blank'] += row['blank_lines']
    d['comment'] += row['comment_lines']
    d['code'] += row['code_lines']

active_rows = [r for r in rows if r['category'] == 'active']
legacy_rows = [r for r in rows if r['category'] != 'active']
by_physical = sorted(rows, key=lambda r: (-r['physical_lines'], r['path']))[:20]
by_code = sorted(rows, key=lambda r: (-r['code_lines'], r['path']))[:20]


def git_output(*args):
    try:
        return subprocess.check_output(['git', '-C', str(root), *args], text=True, stderr=subprocess.STDOUT)
    except Exception:
        return ''

commit_count = git_output('rev-list', '--count', 'HEAD').strip() or 'n/a'
first_commit = git_output('log', '--reverse', '--format=%aI', '-1', 'HEAD').strip() or 'n/a'
latest_commit = git_output('log', '--format=%aI', '-1', 'HEAD').strip() or 'n/a'
history = git_output('log', '--format=%H', '--numstat')
added = deleted = 0
for line in history.splitlines():
    parts = line.split('\t')
    if len(parts) >= 3:
        try:
            added += int(parts[0])
            deleted += int(parts[1])
        except ValueError:
            pass
changed_files = set()
for line in history.splitlines():
    if line.startswith('commit ') or line.startswith('Author:') or line.startswith('Date:'):
        continue
    if '\t' not in line and line.strip() and not re.match(r'^\d+$', line):
        changed_files.add(line.strip())

md = []
md.append('# Code Metrics Audit')
md.append('')
md.append('## Summary')
md.append('')
md.append(f'- Included source files: {len(rows)}')
md.append(f'- Active source files: {len(active_rows)}')
md.append(f'- Legacy/duplicate/generated source files: {len(legacy_rows)}')
md.append(f'- Total physical lines (included source files): {sum(r["physical_lines"] for r in rows)}')
md.append(f'- Total code lines (included source files): {sum(r["code_lines"] for r in rows)}')
md.append(f'- Total comment lines: {sum(r["comment_lines"] for r in rows)}')
md.append(f'- Total blank lines: {sum(r["blank_lines"] for r in rows)}')
md.append('')
md.append('## Language Breakdown')
md.append('')
md.append('| Language | Files | Total Lines | Blank | Comments | Code |')
md.append('|---|---:|---:|---:|---:|---:|')
for lang in ['Python', 'Arduino/C++', 'C', 'JavaScript', 'Shell', 'Other']:
    d = lang_totals.get(lang, {'files': 0, 'physical': 0, 'blank': 0, 'comment': 0, 'code': 0})
    md.append(f'| {lang} | {d["files"]} | {d["physical"]} | {d["blank"]} | {d["comment"]} | {d["code"]} |')
md.append('')
md.append('## Component Breakdown')
md.append('')
md.append('| Component | Files | Physical LOC | Code LOC |')
md.append('|---|---:|---:|---:|')
for comp in ['ESP32 Firmware', 'Python Backend', 'Qt GUI', 'Legacy GUI', 'Tests', 'Tools/Scripts', 'Other']:
    d = metrics.get(comp, {'files': 0, 'physical': 0, 'code': 0})
    md.append(f'| {comp} | {d["files"]} | {d["physical"]} | {d["code"]} |')
md.append('')
md.append('## Largest Files by Physical Lines')
md.append('')
md.append('| Path | Language | Physical | Blank | Comments | Code |')
md.append('|---|---|---:|---:|---:|---:|')
for r in by_physical:
    md.append(f'| {r["path"]} | {r["language"]} | {r["physical_lines"]} | {r["blank_lines"]} | {r["comment_lines"]} | {r["code_lines"]} |')
md.append('')
md.append('## Largest Files by Code Lines')
md.append('')
md.append('| Path | Language | Physical | Blank | Comments | Code |')
md.append('|---|---|---:|---:|---:|---:|')
for r in by_code:
    md.append(f'| {r["path"]} | {r["language"]} | {r["physical_lines"]} | {r["blank_lines"]} | {r["comment_lines"]} | {r["code_lines"]} |')
md.append('')
md.append('## Excluded / Special Cases')
md.append('')
md.append('- Excluded directories: ' + ', '.join(sorted(exclude_dirs)))
md.append('- Archive, legacy, experimental, duplicate, backup, and generated files were included in the inventory and reported separately as non-active source.')
md.append('')
md.append('## Git History')
md.append('')
md.append(f'- Commits: {commit_count}')
md.append(f'- First commit date: {first_commit}')
md.append(f'- Latest commit date: {latest_commit}')
md.append(f'- Files changed in history (unique): {len(changed_files)}')
md.append(f'- Historical lines added: {added}')
md.append(f'- Historical lines deleted: {deleted}')
md.append(f'- Historical net change: {added - deleted}')
md.append('')
md.append('## Methodology')
md.append('')
md.append('- Source files were discovered by extension across the repository tree.')
md.append('- Excluded directories were skipped, including .git, virtual environments, caches, build artifacts, and dependency folders.')
md.append('- Physical lines are counted directly from file contents. Blank lines are whitespace-only. Comment-only lines are detected with language-aware heuristics; code lines are the remainder.')
md.append('- Legacy/duplicate/generated files are called out separately so the headline totals can distinguish active source from archived or copy-like files.')

(docs_dir / 'CODE_METRICS.md').write_text('\n'.join(md), encoding='utf-8')

print('SOURCE_FILES', len(rows))
print('ACTIVE_SOURCE_FILES', len(active_rows))
print('LEGACY_SOURCE_FILES', len(legacy_rows))
print('TOTAL_PHYSICAL_LINES', sum(r['physical_lines'] for r in rows))
print('TOTAL_BLANK_LINES', sum(r['blank_lines'] for r in rows))
print('TOTAL_COMMENT_LINES', sum(r['comment_lines'] for r in rows))
print('TOTAL_CODE_LINES', sum(r['code_lines'] for r in rows))
print('LANGUAGES')
for lang in ['Python', 'Arduino/C++', 'C', 'JavaScript', 'Shell', 'Other']:
    d = lang_totals.get(lang, {'files': 0, 'physical': 0, 'blank': 0, 'comment': 0, 'code': 0})
    print(lang, d)
print('COMPONENTS')
for comp in ['ESP32 Firmware', 'Python Backend', 'Qt GUI', 'Legacy GUI', 'Tests', 'Tools/Scripts', 'Other']:
    d = metrics.get(comp, {'files': 0, 'physical': 0, 'code': 0})
    print(comp, d)
print('TOP_PHYSICAL')
for r in by_physical:
    print(r['path'], r['physical_lines'], r['code_lines'])
print('TOP_CODE')
for r in by_code:
    print(r['path'], r['code_lines'], r['physical_lines'])
print('GIT', commit_count, first_commit, latest_commit, len(changed_files), added, deleted, added - deleted)
