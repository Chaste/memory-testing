# memory-testing

Generated files from the memory testing CI.

It is unlilely you should be interacting with this repository.
Index files are added by the [Chaste memory testing workflow](https://github.com/Chaste/Chaste/blob/develop/.github/workflows/memory-testing.yml).

:warning: If fiddling with this manually is essential, then:

## Requirements

- Python 3.11+ (tested)
- `pip install -r requirements.txt`

## Usage

1. Place log directories (with `index.html`) or `.tar.xz` archives under `log-files/`.
2. Run `python write_index.py`.
3. Open `log-files/index.html` in a browser.
