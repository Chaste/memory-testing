# memory-testing

Generated files from the memory testing CI.

It is unlilely you should be interacting with this repository.
Log directories and archives are added by the [Chaste memory testing workflow](https://github.com/Chaste/Chaste/blob/develop/.github/workflows/tier-1-memory-testing.yml).
`log-files/index.html` is generated at GitHub Pages deploy time (see `.github/workflows/static.yml`) and is not committed.

:warning: If fiddling with this manually is essential, then:

## Requirements

- Python 3.11+ (tested)
- `write_index.py` and `archive_old.py` use only the standard library.
- The history-rewriting steps below need `pip install -r requirements.txt` (for `git-filter-repo`).

## Usage

1. Place log directories (with `index.html`) or `.tar.xz` archives under `log-files/`.
2. Run `python write_index.py`.
3. Open `log-files/index.html` in a browser (it is gitignored, not committed).

## Archiving old files and re-writing history

:warning: :warning: :warning: this is highly destructive.
Only follow these instructions if you're certain you know what you're doing.

To keep this repo (specifically, the working tree) relatively small, with plenty of space to upload to GitHub pages, we periodically archive old plaintext files and replace them with a .tar.xz.

We, additionally, purge the history of the old text files, which helps keep the repository itself a manageable size.

By default, we archive all records older than one year.

1. `pip install -r requirements.txt`
2. From the root directory: `python archive_old.py`
3. Check, and commit `.tar.xz` files
4. From the root directory: `python amend_history.py`
5. CHECK THAT THE AMENDED HISTORY LOOKS GOOD
6. Add origin back: `git remote add origin git@github.com:Chaste/memory-testing.git`
7. DOUBLE CHECK EVERYTHING LOOKS GOOD
8. `git push --force --all`
9. `git push --force --tags`

`log-files/index.html` will be regenerated automatically by the Pages deploy workflow on push; no need to rewrite or commit it manually.
