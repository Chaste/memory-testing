"""
Script to compress old log directories.

- Run from repository root
- Looks under ./log-files
- Directory names assumed to be YYYY-MM-DD_HH-MM-SS
- Directories older than 1 year are archived to .tar.xz
- Assumes `tar` and `xz` are available
"""

from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
import subprocess
import tempfile

LOG_ROOT = Path("log-files")
DEFAULT_DAYS = 365


def get_cutoff(days: int = DEFAULT_DAYS) -> datetime:
    """Return the cutoff datetime; directories older than this should be archived."""
    return datetime.now() - timedelta(days=days)


def parse_timestamp(name: str) -> Optional[datetime]:
    """
    Parse a directory name of the form YYYY-MM-DD_HH-MM-SS.
    Return a datetime on success, or None if the name does not match.
    """
    try:
        return datetime.strptime(name, "%Y-%m-%d_%H-%M-%S")
    except ValueError:
        return None


def find_old_dirs(root: Path, cutoff: datetime) -> List[Path]:
    """
    Return directories under `root` which contain index.html, and whose
    names parse as timestamps and are strictly older than `cutoff`.
    """
    if not root.is_dir():
        return []

    results: List[Path] = []
    for p in sorted(root.iterdir()):
        if not (p.is_dir() and (p / 'index.html').is_file()):
            continue
        ts = parse_timestamp(p.name)
        if ts is None:
            continue
        if ts < cutoff:
            results.append(p)
    return results


def compress_dir(src: Path) -> None:
    """
    Compress `src` directory to src.tar.xz using `tar | xz -9`.
    Skip if the archive already exists.
    """
    dest = src.with_name(src.name + ".tar.xz")
    if dest.exists():
        return

    with tempfile.NamedTemporaryFile(dir=str(dest.parent), delete=False) as tf:
        tmp = Path(tf.name)

    tar_cmd = ["tar", "-C", str(src.parent), "-c", src.name]
    xz_cmd = ["xz", "-9", "-c"]

    try:
        with open(tmp, "wb") as fout:
            p1 = subprocess.Popen(tar_cmd, stdout=subprocess.PIPE)
            p2 = subprocess.Popen(xz_cmd, stdin=p1.stdout, stdout=fout)
            p1.stdout.close()
            p2.communicate()

            if p1.wait() != 0 or p2.returncode != 0:
                raise RuntimeError("tar/xz failed")

        tmp.replace(dest)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def main() -> None:
    cutoff = get_cutoff()
    old_dirs = find_old_dirs(LOG_ROOT, cutoff)

    for src in old_dirs:
        print(f"Compressing {src} ...", end="", flush=True)
        try:
            compress_dir(src)
            print(" done")
        except Exception as e:
            print(f" ERROR: {e}")


if __name__ == "__main__":
    main()
