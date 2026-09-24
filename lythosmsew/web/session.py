"""
The one working session the server keeps.

Kept apart from the HTTP layer: there is no network here, only "take a
dictionary of inputs, run the analysis, give the results back as a
dictionary". Everything the interface does can therefore be tested without
opening a socket.

A wall analysis, the search for the required length included, takes a
fraction of a second and runs inline. A height study analyses and designs a
wall at every height of the range: it runs in a thread, reports progress
through `state()`, and can be cancelled.
"""

from __future__ import annotations

import threading
import traceback
from typing import Any, Dict, Optional

from .. import forms, height_plots, heights, render, report, summary
from ..engine import MSEWall, MSEWError, generate_layers
from ..heights import HeightStudy
from ..i18n import TRANSLATIONS, t
from .strings import shell_strings

#: Languages the interface offers
LANGS = ("en", "tr")


class Session:
    """The single analysis session the server knows about."""

    def __init__(self, lang: str = "en", theme: str = "light"):
        self.lock = threading.Lock()
        self.lang = lang if lang in LANGS else "en"
        self.theme = theme
        self.wall: Optional[MSEWall] = None
        self.values: Dict[str, Any] = {}
        self.heights: Optional[HeightStudy] = None
        # background job
        self.job = "idle"                    # idle | running | done | error
        self.job_kind = ""
        self.job_error = ""
        self.job_detail = ""
        self.job_note = ""
        self.done = 0
        self.total = 0
        self.cancelled = False

    # ------------------------------------------------------------------ language
    def set_language(self, lang: str) -> str:
        with self.lock:
            self.lang = lang if lang in LANGS else "en"
            return self.lang

    def set_theme(self, theme: str) -> str:
        with self.lock:
            self.theme = "dark" if theme == "dark" else "light"
            return self.theme

    @property
    def L(self) -> dict:
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["en"])

    def _explain(self, exc: Exception) -> str:
        """An input error in the user's language."""
        if isinstance(exc, MSEWError):
            return t(self.lang, exc.key, **exc.params)
        return str(exc)

    # ------------------------------------------------------------------ what the page loads with
    def meta(self) -> dict:
        """Everything the interface reads on startup: version, texts, schema."""
        from .. import APP_NAME, __version__
        return {
            "app": APP_NAME,
            "version": __version__,
            "language": self.lang,
            "languages": list(LANGS),
            "strings": shell_strings(self.lang),
            "schema": forms.schema(self.lang),
            "defaults": forms.defaults(self.lang),
            "figures": render.PLOT_KEYS,
            "figure_labels": {key: self.L[f"fig_{key}"] for key in render.PLOT_KEYS},
            "height_views": render.HEIGHT_VIEWS,
            "height_view_labels": {view: self.L[f"fig_hs_{view}"]
                                   for view in render.HEIGHT_VIEWS},
        }

    # ------------------------------------------------------------------ job state
    def _begin(self, kind: str, total: int = 0) -> bool:
        with self.lock:
            if self.job == "running":
                return False
            self.job, self.job_kind = "running", kind
            self.job_error = self.job_detail = self.job_note = ""
            self.done, self.total, self.cancelled = 0, total, False
        return True

    def _finish(self, note: str = "") -> None:
        with self.lock:
            self.job, self.job_note = "done", note

    def _fail(self, exc: Exception) -> None:
        with self.lock:
            self.job = "error"
            self.job_error = f"{type(exc).__name__}: {exc}"
            self.job_detail = traceback.format_exc(limit=4)

    def cancel(self) -> dict:
        """Asks a running height study to stop at the next height."""
        with self.lock:
            self.cancelled = True
        return {"ok": True}

    def state(self) -> dict:
        with self.lock:
            return {
                "job": self.job,
                "kind": self.job_kind,
                "error": self.job_error,
                "detail": self.job_detail if self.job == "error" else "",
                "note": self.job_note,
                "done": self.done,
                "total": self.total,
                "has_analysis": self.wall is not None,
                "has_heights": self.heights is not None and bool(self.heights.rows),
            }

    # ================================================================== analysis
    def _external_table(self, wall: MSEWall) -> dict:
        """Static (and seismic) external checks as the summary view's table."""
        L = self.L
        res = wall.results
        name = summary.value_name(L, res["design"])
        columns = ["", f"{name} · {L['plot_static']}", L["res_required"], ""]
        if res["seismic"]:
            columns += [f"{name} · {L['plot_seismic']}", L["res_required"], ""]
        rows = []
        for key in summary.EXTERNAL:
            cells, states = [L[f"chk_{key}"]], [""]
            sets = [res["external"]] + ([res["seismic"]["external"]] if res["seismic"] else [])
            for checks in sets:
                check = checks[key]
                nd = 3 if check["kind"] == "limit" else 2
                text, state = summary.status_text(L, check["status"])
                cells += [summary.num(check["value"], nd), summary.num(check["required"], nd),
                          text]
                states += ["", "", state]
            rows.append({"cells": cells, "states": states})
        return {"columns": columns, "rows": rows}

    def analyse(self, values: dict) -> dict:
        """Runs the wall analysis on the interface's values."""
        try:
            wall = MSEWall(forms.to_config(values))
            wall.run()
        except MSEWError as exc:
            raise ValueError(self._explain(exc)) from exc

        with self.lock:
            self.wall = wall
            self.values = dict(values)

        res = wall.results
        return {
            "ok": True,
            "cards": summary.cards(wall, self.lang),
            "text": summary.results_text(wall, self.lang),
            "headline": summary.headline(wall, self.lang),
            "figures": render.available_figures(wall),
            "warnings": summary.warnings(wall, self.lang),
            "external": self._external_table(wall),
            "bearing": summary.bearing_table(wall, self.lang),
            "layers": summary.layer_table(wall, self.lang),
            "seismic_layers": (summary.layer_table(wall, self.lang, seismic=True)
                               if res["seismic"] else None),
            "all_ok": summary.all_ok(res),
            "required_length": res["required_length"],
        }

    def generate(self, values: dict) -> dict:
        """The layers the layout rule gives for the wall's height."""
        cfg = forms.to_config(values)
        lay = cfg["layout"]
        names = [rtype["name"] for rtype in cfg["reinforcement_types"]]
        rtype = lay["type"] if lay["type"] in names else (names[0] if names else "")
        try:
            layers = generate_layers(cfg["geometry"]["H"], lay["z1"], lay["Sv"], lay["rule"],
                                     lay["ratio"], lay["L"], lay["L_min"], rtype)
        except MSEWError as exc:
            raise ValueError(self._explain(exc)) from exc
        return {"ok": True, "layers": layers}

    # ------------------------------------------------------------------ figures
    def plot(self, target: str, kind: str) -> bytes:
        """The requested figure as PNG."""
        if target == "heights":
            with self.lock:
                study, theme = self.heights, self.theme
            if study is None or not study.rows:
                raise ValueError(self.L["hs_no_data"])
            return render.figure_to_png(render.height_figure(study, kind, self.lang, theme))

        with self.lock:
            wall, theme = self.wall, self.theme
        if wall is None:
            raise ValueError(shell_strings(self.lang)["no_results"])
        return render.figure_to_png(render.analysis_figure(wall, kind, self.lang, theme))

    # ================================================================== height study
    def start_heights(self, values: dict) -> dict:
        """Starts the height study in the background."""
        try:
            cfg = forms.to_config(values)
            h = cfg["heights"]
            study = HeightStudy(cfg, h["H_min"], h["H_max"], h["step"])
            if cfg["layout"]["type"] not in {r["name"] for r in cfg["reinforcement_types"]}:
                raise MSEWError("err_unknown_type", name=cfg["layout"]["type"])
        except Exception as exc:
            return {"ok": False, "error": self.L["hs_failed"].format(e=self._explain(exc))}

        if not self._begin("heights", len(study.heights)):
            return {"ok": False, "error": shell_strings(self.lang)["busy"]}
        with self.lock:
            self.heights = None
        threading.Thread(target=self._run_heights, args=(study,), daemon=True).start()
        return {"ok": True}

    def _run_heights(self, study: HeightStudy) -> None:
        def progress(done: int, total: int) -> None:
            with self.lock:
                self.done, self.total = done, total

        def cancel_asked() -> bool:
            with self.lock:
                return self.cancelled

        try:
            study.run(progress=progress, is_cancelled=cancel_asked)
            with self.lock:
                self.heights = study
                cancelled = self.cancelled
            note = self.L["hs_done"].format(n=len(study.rows))
            if cancelled:
                note = f"{note} {self.L['hs_cancelled']}"
            self._finish(note)
        except Exception as exc:
            self._fail(exc)

    def heights_payload(self) -> dict:
        """What the height study view shows: the verdict, the text and the table."""
        with self.lock:
            study = self.heights
        if study is None or not study.rows:
            return {"ok": False, "error": self.L["hs_no_data"]}
        return {
            "ok": True,
            "n": len(study.rows),
            "verdict": height_plots.verdict(study, self.L),
            "text": height_plots.summary_text(study, self.L),
            "table": height_plots.table(study, self.L),
            "views": render.HEIGHT_VIEWS,
        }

    def export_heights(self, kind: str, path: str) -> str:
        """Writes the height study as CSV or XLSX and returns the path."""
        with self.lock:
            study = self.heights
        if study is None or not study.rows:
            raise ValueError(self.L["hs_no_data"])
        (heights.to_csv if kind == "csv" else heights.to_xlsx)(study, path)
        return path

    # ================================================================== report
    def report(self, fmt: str, path: str) -> str:
        """Writes the calculation report in the chosen format; returns the path."""
        with self.lock:
            wall, study = self.wall, self.heights
        if wall is None:
            raise ValueError(shell_strings(self.lang)["no_results"])
        writer = {"pdf": report.export_pdf, "html": report.export_html,
                  "docx": report.export_docx}.get(fmt)
        if writer is None:
            raise ValueError(f"unknown report format: {fmt}")
        writer(path, wall, self.lang, study if study is not None and study.rows else None)
        return path

    # ================================================================== project files
    def project_file(self, values: dict) -> dict:
        """What `Save` downloads."""
        return forms.project_file(values)

    def load_project(self, data: dict) -> dict:
        """Flat interface values from a project file, defaults filling the gaps."""
        if not isinstance(data, dict) or data.get("format") not in (None, forms.FILE_FORMAT):
            raise ValueError(shell_strings(self.lang)["bad_file"])
        return {"ok": True, "values": forms.from_config(data, forms.defaults(self.lang))}
