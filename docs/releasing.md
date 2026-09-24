# Releasing to PyPI

The distribution is named `lythosmsew`; so are the package you import and the
directory in the repository. The command you type is `lythos-msew`.

## Without a terminal

`tools/upload_to_pypi.py` does everything below from an editor: open it in
Thonny (or IDLE, or VS Code), press Run, and answer the questions in the shell
pane. It builds its own environment for `build` and `twine`, so the system
Python is left alone — on Arch, where pip refuses to install into it, that is
the difference between working and not. Set `TEST_PYPI = True` at the top of
the file to rehearse.

Nothing is sent before it has printed what it is about to upload and you have
answered `yes`.

When it needs the token it opens a small window: paste the token there
(Ctrl+V; it shows as dots) and press **Upload**. If the window is hidden, look
behind the editor or on the taskbar. It takes the token without asking when
the environment variable `PYPI_TOKEN` holds it, or when `~/.pypirc` does (it
offers to save it there after the first upload). Editors have no real console,
and Python's hidden input would wait there for ever, so the token is never
asked for that way outside a terminal.

## Once, before the first upload

Get an API token from <https://pypi.org/manage/account/token/>. Until the
project exists on PyPI the token has to be account-wide; afterwards replace it
with one scoped to `lythosmsew`. Put it in `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...
```

`chmod 600 ~/.pypirc`. The token is a password — it never belongs in the
repository.

## Every release

1. Raise `version` in `pyproject.toml` and `__version__` in
   `lythosmsew/__init__.py`; the test suite checks that the two agree.
   **PyPI accepts a version number once and only once**, so anything wrong in
   the metadata — the author name, the licence, the README that becomes the
   project page — has to be fixed before the upload, not after.
2. Run the tests: `pytest -q`.
3. Build clean:

   ```bash
   rm -rf dist build
   python -m build
   twine check dist/*
   ```

4. Upload:

   ```bash
   twine upload dist/*
   ```

5. Check what was actually published, in an empty environment:

   ```bash
   python -m venv /tmp/check
   /tmp/check/bin/pip install lythosmsew
   /tmp/check/bin/lythos-msew example -o /tmp/check.msew
   /tmp/check/bin/lythos-msew run /tmp/check.msew -o /tmp/check.pdf
   /tmp/check/bin/lythos-msew web --no-browser        # then open the address
   ```

6. Tag it: `git tag v0.1.0 && git push --tags`.

## Rehearsing on TestPyPI

TestPyPI is a separate site with its own account and its own token
(<https://test.pypi.org/manage/account/token/>; add it to `~/.pypirc` under a
`[testpypi]` section):

```bash
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ lythosmsew
```

The second index is needed because NumPy, Matplotlib and reportlab are
not mirrored there. A name used on TestPyPI does not reserve it on PyPI.

## What goes into the wheel

`lythosmsew/web/static/*` is declared as package data in `pyproject.toml`.
Without it the interface serves a blank page, and the tests, which run from
the source tree, would not notice. After building, look:

```bash
python -c "import zipfile; print(zipfile.ZipFile('dist/lythosmsew-0.1.0-py3-none-any.whl').namelist())"
```

Both `tests/test_packaging.py` and the check above exist because this is the
one class of mistake a green test suite will not catch.
