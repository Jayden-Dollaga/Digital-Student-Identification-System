from pathlib import Path
import os

home = Path.home()
root = home / 'AppData' / 'Roaming' / 'Code' / 'User' / 'workspaceStorage'
if not root.exists():
    raise FileNotFoundError(root)

keywords = [
    'Forked: code structure and completion request',
    'code structure and completion request',
    '44a2ea77-9e80-4abf-b1a6-f2beda905f35',
]
exts = {'.json', '.jsonl', '.txt', '.log', '.idx', '.cache', '.dat', '.db', '.sqlite', '.yaml', '.yml', '.md'}

out = []
roots = []
for ws in sorted(root.iterdir(), key=lambda p: p.name):
    if not ws.is_dir():
        continue
    copilot = ws / 'GitHub.copilot-chat'
    if copilot.is_dir():
        roots.append((ws.name, copilot))

out.append(f'ROOT {root}')
out.append(f'EXISTS {root.exists()}')
out.append(f'WORKSPACE_STORAGE_ROOTS {len(roots)}')
for ws_name, copilot in roots:
    out.append(f'')
    out.append(f'WORKSPACE {ws_name}')
    out.append(f'COPILOT_ROOT {copilot}')
    matches = []
    for p in sorted(copilot.rglob('*')):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        try:
            text = p.read_text('utf-8', errors='ignore')
        except Exception:
            continue
        found = [kw for kw in keywords if kw in text]
        if found:
            matched_lines = []
            for i, line in enumerate(text.splitlines(), start=1):
                if any(kw in line for kw in keywords):
                    matched_lines.append((i, line.strip()))
                    if len(matched_lines) >= 5:
                        break
            matches.append((p.relative_to(root), found, matched_lines))
    out.append(f'MATCH_COUNT {len(matches)}')
    for path, found, matched_lines in matches:
        out.append(f'PATH {path}')
        out.append(f'FOUND {found}')
        out.append(f'LINES {len(matched_lines)}')
        for i, line in matched_lines:
            out.append(f'  {i}: {line}')

print('\n'.join(out))
