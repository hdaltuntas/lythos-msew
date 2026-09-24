"""
Upload a Lythos MSEW release to PyPI — works from an editor such as Thonny:
press the green Run button and answer the questions in the shell.

It does what `python -m build && twine upload dist/*` does on a terminal; the
difference is that it makes its own virtual environment to work from, so
nothing is installed into the system Python — on the distributions where pip
refuses to touch it (Arch, recent Debian / Ubuntu) that is the difference
between working and not.

What it does, in order:

    1. makes a small environment in ~/.lythos-release with build and twine in it
    2. rebuilds the distribution if you want it to (dist/ is cleaned first)
    3. compares the version in pyproject.toml with the version of the files
    4. checks whether that version is already published on PyPI
    5. runs `twine check` over the files
    6. finds the API token (see below), or asks for it in a small window
    7. shows what it is about to upload, asks you to confirm, then uploads

Nothing is sent anywhere before step 5, and any answer other than "yes" stops it.

PyPI accepts a version number once and never again. Read what steps 3 and 4
print before you confirm.

The token is looked for in this order:

    · the environment variable PYPI_TOKEN (or TWINE_PASSWORD)
    · ~/.pypirc, if an earlier run saved it there
    · otherwise a small window opens with a field to paste it into (Ctrl+V);
      what is pasted is shown as dots. Without a desktop the shell asks
      instead.

Editors such as Thonny and IDLE have no real console, and Python's hidden
input (getpass) waits there for a keyboard it never reads from — the program
looks frozen. That is why the token is asked for in a window, and never with
getpass outside a real terminal.

The token is not stored unless you say so, not printed and not logged; it is
passed to twine as an environment variable.
"""

import configparser
import getpass
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import venv

# Set this to True to rehearse on TestPyPI instead of the real PyPI. TestPyPI
# is a throwaway copy of the site with its own accounts and its own tokens;
# nothing uploaded there is permanent.
TEST_PYPI = False

PROJECT = "lythosmsew"
COMMAND = "lythos-msew"
ENV = os.path.expanduser("~/.lythos-release")
PYPIRC = os.path.expanduser("~/.pypirc")
REPOSITORY = "testpypi" if TEST_PYPI else "pypi"
SITE = "https://test.pypi.org" if TEST_PYPI else "https://pypi.org"
TOKEN_PAGE = f"{SITE}/manage/account/token/"

HERE = os.path.dirname(os.path.abspath(__file__))


def _is_project(folder):
    """True if the folder holds this project's pyproject.toml."""
    try:
        with open(os.path.join(folder, "pyproject.toml"), encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return False
    return re.search(rf'^name\s*=\s*"{PROJECT}"', text, re.MULTILINE) is not None


def find_project():
    """The project's source folder: the one above tools/ in a clone, or the
    folder the script or the shell is in. None when the script was copied
    somewhere on its own — then it can upload, but not build."""
    for folder in (os.path.join(HERE, ".."), HERE, os.getcwd(),
                   os.path.join(os.getcwd(), "..")):
        folder = os.path.normpath(folder)
        if _is_project(folder):
            return folder
    return None


ROOT = find_project()


def find_dist():
    """The folder holding this project's .whl / .tar.gz files.

    In a clone that is the project's dist/. A copy of this script on its own
    also finds a dist/ folder beside itself (or in the shell's folder), or the
    files lying right next to it.
    """
    candidates = []
    if ROOT:
        candidates.append(os.path.join(ROOT, "dist"))
    candidates += [os.path.join(HERE, "dist"), HERE,
                   os.path.join(os.getcwd(), "dist")]
    for folder in candidates:
        if releases_in(os.path.normpath(folder)):
            return os.path.normpath(folder)
    return os.path.join(ROOT, "dist") if ROOT else os.path.join(HERE, "dist")

# Package name and version, from a distribution file name.
FILENAME = re.compile(r"^(?P<name>[A-Za-z0-9_.-]+?)-(?P<version>\d[^-]*?)"
                      r"(?:-py3-none-any)?\.(?:whl|tar\.gz)$")


# --------------------------------------------------------------------- asking
def ask(question, default=None):
    suffix = f" [{default}]" if default else ""
    try:
        answer = input(f"{question}{suffix}: ").strip()
    except EOFError:
        return default or ""
    return answer or (default or "")


def yes(question, default="no"):
    return ask(f"{question} (yes/no)", default).lower() in ("y", "yes")


def stop(message):
    raise SystemExit(f"\n{message}")


# ---------------------------------------------------------------- environment
def tool(name):
    """The path of a program inside our own environment."""
    binary = "Scripts" if os.name == "nt" else "bin"
    suffix = ".exe" if os.name == "nt" else ""
    return os.path.join(ENV, binary, name + suffix)


def run(command, failure, env=None, cwd=None):
    result = subprocess.run(command, env=env, cwd=cwd)
    if result.returncode != 0:
        stop(f"{failure} (exit code {result.returncode}).")
    return result


def prepare_environment(need_build):
    if not os.path.isfile(tool("python")):
        print(f"Making a small environment in {ENV} ...")
        venv.EnvBuilder(with_pip=True, clear=True).create(ENV)
    wanted = ["twine"] + (["build"] if need_build else [])
    missing = [name for name in wanted if not os.path.isfile(tool(name))]
    if missing:
        print(f"Installing into it: {', '.join(missing)} ...")
        run([tool("python"), "-m", "pip", "install", "--quiet",
             "--disable-pip-version-check", "--upgrade", *missing],
            "The tools could not be installed")
    print("Ready.\n")


# --------------------------------------------------------------------- version
def declared_version():
    """The version written in pyproject.toml."""
    if not ROOT:
        return None
    path = os.path.join(ROOT, "pyproject.toml")
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return match.group(1) if match else None


def published_versions():
    """The versions published on PyPI. Returns None with no network."""
    url = f"{SITE}/pypi/{PROJECT}/json"
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            return set(json.load(response).get("releases", {}))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return set()                 # the project does not exist yet
        return None
    except Exception:
        return None                      # no network; the upload can still be tried


# ----------------------------------------------------------------------- files
def releases_in(folder):
    """The distribution files in a folder, grouped by version."""
    found = {}
    if not os.path.isdir(folder):
        return found
    for entry in sorted(os.listdir(folder)):
        match = FILENAME.match(entry)
        # a dist/ folder shared with other packages must never upload them
        if match and match.group("name").lower().replace("-", "_") == PROJECT:
            key = (match.group("name"), match.group("version"))
            found.setdefault(key, []).append(os.path.join(folder, entry))
    return found


def build_distribution():
    """Cleans the project's dist/ and builds it again."""
    if not ROOT:
        stop(f"There is no {PROJECT} source here to build from: this script was\n"
             f"copied on its own ({HERE}).\n"
             f"Either put the dist folder with the .whl and .tar.gz next to this\n"
             f"script and answer 'no' to rebuilding, or run the copy in the tools\n"
             f"folder of a clone of the repository.")
    prepare_environment(need_build=True)    # build may not be installed yet
    dist = os.path.join(ROOT, "dist")
    if os.path.isdir(dist):
        print(f"Cleaning {dist} ...")
        shutil.rmtree(dist)
    print("Building the distribution ...\n")
    run([tool("python"), "-m", "build"], "The build failed", cwd=ROOT)
    print()


def choose_files():
    dist = find_dist()
    found = releases_in(dist)
    if not found:
        print(f"There is no {PROJECT} .whl or .tar.gz in {dist}.")
        if not ROOT:
            stop(f"Put the dist folder (or the two files) next to this script,\n"
                 f"in {HERE}, and run it again.")
        if not yes("Shall I build it now?", "yes"):
            stop("There is nothing to upload.")
        build_distribution()
        dist = find_dist()
        found = releases_in(dist)
        if not found:
            stop("The build produced nothing.")

    keys = sorted(found)
    print(f"Found in {dist}:")
    for index, (name, version) in enumerate(keys, start=1):
        files = ", ".join(os.path.basename(f) for f in found[(name, version)])
        print(f"  {index}. {name} {version} — {files}")

    if len(keys) == 1:
        key = keys[0]
    else:
        # More than one version is here: uploading the wrong one cannot be
        # undone, so never guess.
        print("\nThere is more than one version here.")
        while True:
            answer = ask("Which number")
            if answer.isdigit() and 1 <= int(answer) <= len(keys):
                key = keys[int(answer) - 1]
                break
            print("Type one of the numbers above.")

    files = found[key]
    if not any(f.endswith(".whl") for f in files):
        print("\nWarning: no .whl, only a source archive.")
    if not any(f.endswith(".tar.gz") for f in files):
        print("\nWarning: no .tar.gz source archive, only a wheel.")
    return key, files


def check_version(name, version):
    """Compares the version with pyproject.toml and with PyPI."""
    declared = declared_version()
    if declared and declared != version:
        print(f"\nWarning: pyproject.toml says {declared}, the files say {version}.")
        print("You have probably raised the version without rebuilding.")
        if not yes("Carry on anyway?"):
            stop("Stopped.")

    published = published_versions()
    if published is None:
        print("\nPyPI could not be reached (no network); the version check was skipped.")
        return
    if version in published:
        stop(f"{name} {version} is already on PyPI. A version number is accepted "
             f"once: raise the version in pyproject.toml and build again.")
    if not published:
        print(f"\n{name} is not on PyPI yet; this will be the first upload.")
        print("For a first upload the token has to be scoped to the entire account —")
        print("a project-scoped token can only be made for a project that exists.")
    else:
        newest = sorted(published)[-1]
        print(f"\nVersions on PyPI: {len(published)} (latest: {newest}).")


# ------------------------------------------------------------------- the token
def stored_token():
    """The token in ~/.pypirc for this repository, if there is one."""
    if not os.path.isfile(PYPIRC):
        return None
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(PYPIRC)
    except configparser.Error:
        return None
    if parser.has_option(REPOSITORY, "password"):
        return parser.get(REPOSITORY, "password")
    return None


def token_from_environment():
    """A token handed over in an environment variable, if there is one."""
    for name in ("PYPI_TOKEN", "TWINE_PASSWORD"):
        value = os.environ.get(name, "").strip()
        if value:
            return name, value
    return None, None


def real_terminal():
    """True in a real console; False in an editor's shell (Thonny, IDLE)."""
    try:
        return sys.stdin is not None and sys.stdin.isatty() and "idlelib" not in sys.modules
    except (AttributeError, ValueError):
        return False


def ask_in_window():
    """A small window with a hidden field to paste the token into.

    Returns the token, "" if the window was closed or cancelled, or None when
    no window can be shown (no tkinter, no desktop).
    """
    try:
        import tkinter as tk
    except ImportError:
        return None
    try:
        root = tk.Tk()
    except Exception:                       # no display
        return None

    result = {"token": ""}
    root.title("PyPI token")
    root.resizable(False, False)
    root.attributes("-topmost", True)       # in front of the editor

    frame = tk.Frame(root, padx=16, pady=14)
    frame.pack()
    tk.Label(frame, justify="left",
             text=f"Paste the API token (Ctrl+V) and press Upload.\n"
                  f"It starts with 'pypi-'. Get one at {TOKEN_PAGE}").pack(anchor="w")
    entry = tk.Entry(frame, width=58, show="•")
    entry.pack(fill="x", pady=(10, 4))

    shown = tk.BooleanVar(value=False)
    tk.Checkbutton(frame, text="Show what I pasted", variable=shown,
                   command=lambda: entry.config(show="" if shown.get() else "•")
                   ).pack(anchor="w")

    def accept(_event=None):
        result["token"] = entry.get().strip()
        root.destroy()

    def cancel(_event=None):
        result["token"] = ""
        root.destroy()

    buttons = tk.Frame(frame)
    buttons.pack(anchor="e", pady=(10, 0))
    tk.Button(buttons, text="Cancel", width=10, command=cancel).pack(side="right")
    tk.Button(buttons, text="Upload", width=10, command=accept).pack(side="right", padx=6)
    root.bind("<Return>", accept)
    root.bind("<Escape>", cancel)
    root.protocol("WM_DELETE_WINDOW", cancel)

    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_reqwidth()) // 2
    y = (root.winfo_screenheight() - root.winfo_reqheight()) // 3
    root.geometry(f"+{x}+{y}")
    root.lift()
    root.focus_force()
    entry.focus_set()
    root.mainloop()
    return result["token"]


def ask_in_shell():
    """The token typed into the shell: hidden in a real console, visible in an
    editor, where hidden input would hang."""
    if real_terminal():
        return getpass.getpass("Token (what you type stays hidden): ").strip()
    print("(This shell has no hidden input: the token will be visible as you paste it.)")
    return ask("Token")


def get_token():
    """Finds the token, or asks for it. Returns (token, is new, where it came from)."""
    variable, token = token_from_environment()
    if token:
        print(f"Using the token in the environment variable {variable}.\n")
        return token, False, f"the environment variable {variable}"
    token = stored_token()
    if token:
        print(f"Using the token in {PYPIRC}.\n")
        return token, False, PYPIRC

    print(f"An API token is needed. Get one at {TOKEN_PAGE}.")
    print("  · it starts with 'pypi-' and is shown only once")
    print("  · for a project's first upload the scope must be the entire account")
    print("  · once the project is published, replace it with a project token\n")
    print("Opening a small window: paste the token there (Ctrl+V) and press Upload.")
    print("If you cannot see it, look behind the editor or on the taskbar.\n")

    token = ask_in_window()
    if token is None:                       # no window could be shown
        print("(No window could be opened; the token is asked for here instead.)")
        token = ask_in_shell()
    token = token.strip()
    if not token:
        stop("No token, no upload. Nothing was sent.")
    if not token.startswith("pypi-"):
        print("\nThat does not look like a token — tokens start with 'pypi-'.")
        if not yes("Use it anyway?"):
            stop("Stopped. Nothing was sent.")
    print("Token received.")
    return token, True, "pasted"


def offer_to_save(token):
    print(f"\nThe token can be kept in {PYPIRC} and never asked for again.")
    print("It is a password: the file is written so that only you can read it.")
    if not yes("Save it?"):
        return
    parser = configparser.ConfigParser(interpolation=None)
    if os.path.isfile(PYPIRC):
        parser.read(PYPIRC)
    if not parser.has_section(REPOSITORY):
        parser.add_section(REPOSITORY)
    parser.set(REPOSITORY, "username", "__token__")
    parser.set(REPOSITORY, "password", token)
    # Create it with the right permissions from the start, rather than writing
    # the token first and narrowing the file afterwards.
    handle = os.open(PYPIRC, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(handle, "w", encoding="utf-8") as fh:
        parser.write(fh)
    os.chmod(PYPIRC, 0o600)
    print(f"Saved to {PYPIRC}.")


def explain_failure(name, source):
    """If the upload fails, says what the likeliest reasons are."""
    print("\n" + "-" * 62)
    print("The upload was refused. The usual reasons:")
    print()
    print("  403 Forbidden — the token's scope may be wrong. A token scoped to")
    print(f"     another project (lythosspwa, say) does not work for {name}.")
    print("     For a first upload, make a token scoped to the entire account:")
    print(f"     {TOKEN_PAGE}")
    print("     Tokens do not expire; they last until they are revoked.")
    print()
    print("  400 File already exists — this version is published already. Raise")
    print("     the version in pyproject.toml and build again.")
    print()
    print("  Read twine's own message above the line: it names the reason.")
    print()
    if source == "pasted":
        print("  The token used was the one pasted in: make a new one scoped to the")
        print("     entire account and run this again.")
    else:
        print(f"  The token used came from {source}; if it is the wrong one, remove")
        print("     it there and this script will ask for one.")
    print("-" * 62)


# ----------------------------------------------------------------- the main flow
def main():
    where = ("TestPyPI (a rehearsal — nothing uploaded there is permanent)"
             if TEST_PYPI else "PyPI (the real one)")
    print(f"Target: {where}\n")

    if ROOT:
        print(f"Project: {ROOT}\n")
        rebuild = yes("Rebuild the distribution?", "yes")
    else:
        print(f"No {PROJECT} source here; the files already built will be uploaded.\n")
        rebuild = False
    prepare_environment(need_build=rebuild)
    if rebuild:
        build_distribution()

    (name, version), files = choose_files()
    check_version(name, version)

    print("\nChecking the files ...")
    run([tool("twine"), "check", *files], "The files did not pass the check")

    print("\n" + "-" * 62)
    print(f"About to upload: {name} {version}")
    for path in files:
        print(f"    {os.path.basename(path)}  "
              f"({os.path.getsize(path) / 1024:.0f} kB)")
    print(f"  target: {where}")
    print("\nA version number is accepted once and never again. If anything is")
    print("wrong, stop here, fix it, raise the version and build again.")
    print("-" * 62 + "\n")
    if not yes("Upload now?"):
        stop("Stopped. Nothing was sent.")

    token, is_new, source = get_token()

    environment = dict(os.environ)
    environment["TWINE_USERNAME"] = "__token__"
    environment["TWINE_PASSWORD"] = token
    environment["TWINE_NON_INTERACTIVE"] = "1"
    if TEST_PYPI:
        environment["TWINE_REPOSITORY"] = "testpypi"

    print("\nUploading ...\n")
    result = subprocess.run([tool("twine"), "upload", *files], env=environment)
    if result.returncode != 0:
        explain_failure(name, source)
        stop(f"The upload failed (exit code {result.returncode}).")

    print(f"\nDone. {SITE}/project/{name}/{version}/")
    print(f"Anyone can now run:  pip install {name}")
    print("\nTo check it, in an empty environment:")
    print("    python -m venv /tmp/check")
    print(f"    /tmp/check/bin/pip install {name}")
    print(f"    /tmp/check/bin/{COMMAND} --version")

    if is_new:
        offer_to_save(token)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as reason:
        print(reason)
    except KeyboardInterrupt:
        print("\nStopped.")
