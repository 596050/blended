#!/usr/bin/env python3
"""Commit the verified corpus index with an explicit automation identity."""
import argparse
from pathlib import Path
import subprocess
import time


def commit_staged_corpus(repository: Path, message: str, *, timestamp: int | None = None) -> str:
    if not message.strip() or '\0' in message:
        raise ValueError('A non-empty commit message without NUL is required')
    git = ['git', '-C', str(repository.resolve())]
    ref = subprocess.check_output(git + ['symbolic-ref', 'HEAD'], text=True).strip()
    if not ref.startswith('refs/heads/'):
        raise ValueError('Publication must use a branch, not detached HEAD')
    previous = subprocess.run(git + ['rev-parse', '--verify', 'HEAD'], capture_output=True, text=True)
    parent = previous.stdout.strip() if previous.returncode == 0 else None
    tree = subprocess.check_output(git + ['write-tree'], text=True).strip()
    epoch = int(time.time()) if timestamp is None else timestamp
    if not isinstance(epoch, int) or epoch < 0:
        raise ValueError('Invalid commit timestamp')
    identity = f'github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> {epoch} +0000'
    lines = [f'tree {tree}'] + ([f'parent {parent}'] if parent else [])
    raw = ('\n'.join(lines + ['author ' + identity, 'committer ' + identity, '', message.rstrip(), ''])).encode()
    commit = subprocess.check_output(git + ['hash-object', '-t', 'commit', '-w', '--stdin'], input=raw).decode().strip()
    subprocess.run(git + ['update-ref', ref, commit, parent or '0' * 40], check=True)
    return commit


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repository', type=Path, required=True)
    p.add_argument('--message', required=True)
    a = p.parse_args()
    print(commit_staged_corpus(a.repository, a.message))
