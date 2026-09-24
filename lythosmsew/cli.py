"""Command line interface."""

from __future__ import annotations

import argparse
import json
import sys

from . import APP_NAME, __version__

#: Default port of the local interface (the family counts up from 8777)
PORT = 8782


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="lythos-msew",
        description="Mechanically stabilised earth walls: external stability (sliding, "
                    "overturning, eccentricity, bearing capacity by Terzaghi, Meyerhof, "
                    "Hansen, Vesić and EN 1997-1), internal stability of steel strip and "
                    "geosynthetic reinforcement (tensile, pullout, connection), seismic "
                    "loading, ASD or LRFD, and a study over the wall height.")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    # Running the program with no subcommand means "web", so the top level
    # carries that subcommand's defaults: without them the bare `lythos-msew`
    # would reach serve() with a Namespace that has no host, port or language.
    parser.set_defaults(host="127.0.0.1", port=PORT, lang="en", no_browser=False)
    sub = parser.add_subparsers(dest="command")

    web = sub.add_parser("web", help="start the interface in a browser")
    web.add_argument("--port", type=int, default=PORT)
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--lang", default="en", choices=["en", "tr"])
    web.add_argument("--no-browser", action="store_true")

    run = sub.add_parser("run", help="analyse a project file and print the results")
    run.add_argument("project", help="path to a .msew / .json project file")
    run.add_argument("-o", "--out", default=None,
                     help="write a report here (.pdf / .html / .docx)")
    run.add_argument("--lang", default="en", choices=["en", "tr"])

    study = sub.add_parser("heights", help="run the height study of a project file")
    study.add_argument("project", help="path to a .msew / .json project file")
    study.add_argument("-o", "--out", default=None, help="write the table here (.csv / .xlsx)")
    study.add_argument("--lang", default="en", choices=["en", "tr"])

    example = sub.add_parser("example", help="write a starter project file")
    example.add_argument("-o", "--out", default="project.msew")

    args = parser.parse_args(argv)
    command = args.command or "web"
    try:
        return _dispatch(command, args)
    except (ValueError, RuntimeError, OSError) as exc:
        # The analysis refuses impossible input with a sentence worth reading
        # (a layer above the wall, a backslope steeper than the fill, an
        # unreadable project file). A traceback would bury it, so only
        # unexpected failures keep theirs.
        print(f"{APP_NAME}: {exc}", file=sys.stderr)
        return 1


def _dispatch(command: str, args) -> int:
    """Runs one command; raises on anything that goes wrong."""
    if command == "web":
        from .web.server import serve
        serve(host=args.host, port=args.port, open_browser=not args.no_browser,
              lang=args.lang)
        return 0

    from . import forms

    if command == "example":
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(forms.project_file(forms.defaults()), fh, indent=2, ensure_ascii=False)
        print(args.out)
        return 0

    with open(args.project, encoding="utf-8") as fh:
        data = json.load(fh)

    from .web.session import Session
    session = Session(lang=args.lang)
    values = session.load_project(data)["values"]

    if command == "run":
        result = session.analyse(values)
        print(result["text"])
        if args.out:
            fmt = args.out.lower().rsplit(".", 1)[-1]
            print(session.report(fmt if fmt in ("pdf", "html", "docx") else "pdf", args.out))
        return 0

    # The height study: analyse the wall first, so the report has something to
    # sit beside, then design it at every height.
    session.analyse(values)
    started = session.start_heights(values)
    if not started["ok"]:
        print(started["error"], file=sys.stderr)
        return 1
    import time
    last = -1
    while session.state()["job"] == "running":
        state = session.state()
        if state["total"] and state["done"] != last:
            last = state["done"]
            print(f"\r{state['done']} / {state['total']}", end="", file=sys.stderr, flush=True)
        time.sleep(0.1)
    print("", file=sys.stderr)
    state = session.state()
    if state["job"] == "error":
        print(state["error"], file=sys.stderr)
        return 1
    payload = session.heights_payload()
    if not payload["ok"]:
        print(payload["error"], file=sys.stderr)
        return 1
    print(payload["text"])
    if args.out:
        kind = "xlsx" if args.out.lower().endswith(".xlsx") else "csv"
        print(session.export_heights(kind, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
