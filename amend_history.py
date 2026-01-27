#!/usr/bin/env python3
"""
purge_dirs_history.py

- Run from repository root (where .git lives).
- Assumes *.tar.xz archives already committed.
- For each log-files/NAME.tar.xz where log-files/NAME exists:
    - git rm -r log-files/NAME
    - commit a single change replacing those directories (archives remain)
    - run git-filter-repo to remove the directories from all history
    - expire reflog & aggressive gc
- Does NOT push; you must run:
      git push --force --all
      git push --force --tags
"""

from pathlib import Path
from typing import List
import subprocess
import tempfile
import os
import sys

LOG_ROOT = Path("log-files")


def run(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, text=True)


def check_repo_root() -> None:
    if not (Path(".git").exists() and Path(".git").is_dir()):
        print("ERROR: .git not found. Run from repository root.", file=sys.stderr)
        sys.exit(2)


def ensure_clean_worktree() -> None:
    out = subprocess.run(["git", "status", "--porcelain"], stdout=subprocess.PIPE, text=True)
    if out.stdout.strip():
        print("ERROR: working tree not clean. Commit or stash before running.", file=sys.stderr)
        sys.exit(3)


def find_dirs_with_archives(root: Path = LOG_ROOT) -> List[Path]:
    """
    Return list of directories (Path objects) for which a corresponding .tar.xz exists:
    e.g. root/NAME.tar.xz and root/NAME (dir).
    """
    if not root.is_dir():
        return []
    results: List[Path] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_file():
            continue
        if not entry.name.endswith(".tar.xz"):
            continue
        name = entry.name[:-7]  # strip ".tar.xz"
        candidate = root / name
        if candidate.is_dir() and (candidate / 'index.html').is_file():
            results.append(candidate)
    return results


def commit_removals(dirs: List[Path]) -> None:
    if not dirs:
        return
    # git rm -r each directory
    for d in dirs:
        run(["git", "rm", "-r", str(d)])
    run(["git", "commit", "-m", "Removing logs that have already been archived"])


def write_paths_file(dirs: List[Path]) -> Path:
    """
    Write the list of paths to be removed from history to a file
    in the repository root. Returns the Path to that file.
    """
    paths_file = Path("paths-removed-from-history.txt")

    with paths_file.open("w", newline="\n") as f:
        for d in dirs:
            f.write(d.as_posix() + "\n")

    return paths_file


def run_filter_repo(paths_file: str) -> None:
    run(["git", "filter-repo", "--invert-paths", f"--paths-from-file={paths_file}", "--force"])


def expire_and_gc() -> None:
    run(["git", "reflog", "expire", "--expire=now", "--all"])
    run(["git", "repack", "-Adf"])
    run(["git", "gc", "--prune=now", "--aggressive"])


def main() -> None:
    check_repo_root()
    ensure_clean_worktree()

    dirs = find_dirs_with_archives()
    if not dirs:
        print("No matching archives + directories found under", LOG_ROOT)
        return

    print("Will remove these directories (including from history):")
    for d in dirs:
        print(f"  {d}")

    commit_removals(dirs)

    paths_file = write_paths_file(dirs)
    try:
        run_filter_repo(paths_file)
    finally:
        try:
            os.unlink(paths_file)
        except Exception:
            pass

    expire_and_gc()

    print("\nHistory purge complete. Inspect repository!")


if __name__ == "__main__":
    main()
