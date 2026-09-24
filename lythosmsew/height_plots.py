"""
The figures and the text of the height study.

    margins   every check's margin — value over required, 1 at the limit —
              against the wall height, so the height at which the first
              check gives out can be read off
    length    the reinforcement length the checks need at each height,
              beside the length the rule lays out and FHWA's minimum
"""

from __future__ import annotations

import math

import numpy as np
from matplotlib.figure import Figure

from .config import PLOT_PALETTE
from .heights import CHECKS
from .plot_style import TITLE_FONT, style_axis, style_figure
from .plotting import CHECK_COLORS

#: The height study figures
VIEWS = ["margins", "length"]


def _legend(ax, th, **kw) -> None:
    legend = ax.legend(fontsize=8, frameon=True, **kw)
    legend.get_frame().set_facecolor(th["panel"])
    legend.get_frame().set_edgecolor(th["border"])
    for text in legend.get_texts():
        text.set_color(th["fg"])


def _title(fig, th, L, key: str, titles: bool) -> None:
    if titles:
        fig.suptitle(L[f"fig_hs_{key}"], fontfamily=TITLE_FONT, fontsize=12.5, color=th["fg"])


def plot_margins(fig: Figure, study, L: dict, theme="light", titles: bool = True) -> None:
    th = style_figure(fig, theme)
    ax = fig.add_subplot(111)
    style_axis(ax, th)
    rows = [r for r in study.rows if r.get("ok")]
    H = np.array([r["H"] for r in rows])
    top = 2.0
    for key, _ in CHECKS:
        values = np.array([r.get(f"m_{key}", math.nan) for r in rows], dtype=float)
        if not np.any(np.isfinite(values)):
            continue
        name = L["chk_internal_sliding"] if key == "internal_sliding" else L[f"card_{key}"]
        ax.plot(H, values, marker="o", markersize=3.5, linewidth=1.7,
                color=CHECK_COLORS[key], label=name)
        top = max(top, min(float(np.nanmax(values)), 8.0))
    if study.seismic:
        for key in ("sliding", "bearing", "pullout"):
            values = np.array([r.get(f"m_seis_{key}", math.nan) for r in rows], dtype=float)
            if np.any(np.isfinite(values)):
                ax.plot(H, values, linestyle="--", linewidth=1.3, color=CHECK_COLORS[key],
                        label=f"{L['card_' + key]} · {L['plot_seismic']}")
    ax.axhline(1.0, color=PLOT_PALETTE["required"], linewidth=1.4, linestyle="--",
               label=L["plot_limit"])
    # shade the heights at which a check fails
    step = (study.heights[1] - study.heights[0]) if len(study.heights) > 1 else 0.5
    for row in study.rows:
        if row.get("status") == "NOT OK":
            ax.axvspan(row["H"] - step / 2, row["H"] + step / 2, color=PLOT_PALETTE["bad"],
                       alpha=0.08, linewidth=0)
    ax.set_ylim(0, top * 1.08)
    if H.size:
        ax.set_xlim(H.min(), H.max() if H.max() > H.min() else H.min() + 1)
    ax.set_xlabel(L["plot_H"])
    ax.set_ylabel(L["plot_margin"])
    _legend(ax, th, loc="upper right", ncol=2)
    _title(fig, th, L, "margins", titles)


def plot_length(fig: Figure, study, L: dict, theme="light", titles: bool = True) -> None:
    th = style_figure(fig, theme)
    ax = fig.add_subplot(111)
    style_axis(ax, th)
    rows = [r for r in study.rows if r.get("ok")]
    H = np.array([r["H"] for r in rows])
    req = np.array([r["required_length"] if math.isfinite(r["required_length"]) else math.nan
                    for r in rows])
    rule = np.array([r["L"] for r in rows])
    fhwa = np.array([r["rule"] for r in rows])
    ax.plot(H, req, marker="o", markersize=4, linewidth=2.0, color=PLOT_PALETTE["demand"],
            label=L["plot_required"])
    ax.plot(H, rule, linewidth=1.6, color=PLOT_PALETTE["capacity"], label=L["plot_rule_L"])
    ax.plot(H, fhwa, linewidth=1.2, linestyle="--", color=th["fg_dim"], label=L["plot_min_L"])
    ax.fill_between(H, np.maximum(np.nan_to_num(req), fhwa), rule,
                    where=rule < np.maximum(np.nan_to_num(req), fhwa),
                    color=PLOT_PALETTE["bad"], alpha=0.15, interpolate=True)
    ax.set_xlabel(L["plot_H"])
    ax.set_ylabel(L["plot_length"])
    ax.set_ylim(bottom=0)
    _legend(ax, th, loc="upper left")
    _title(fig, th, L, "length", titles)


def summary_text(study, L: dict) -> str:
    """The height study as text: the range, the limit height and the table."""
    from .summary import num
    rows = study.rows
    lay = study.config["layout"]
    rule = (f"L = {lay['ratio']:.2f}·H ≥ {lay['L_min']:.2f} m" if lay["rule"] == "ratio"
            else f"L = {lay['L']:.2f} m")
    rule += f", Sv = {lay['Sv']:.3f} m, {lay['type']}"
    lines = [L["hs_title"], "-" * 96,
             L["hs_info"].format(n=len(rows), lo=study.heights[0], hi=study.heights[-1],
                                 design=L[f"design_short_{study.design}"], rule=rule)]
    lines.append(verdict(study, L))
    head = [L["hs_col_H"], L["hs_col_L"], L["hs_col_n"], L["hs_col_req"]] + \
        [L["chk_internal_sliding"] if k == "internal_sliding" else L[f"card_{k}"] for k, _ in CHECKS] + \
        [L["hs_col_status"]]
    lines += ["", "  " + "".join(f"{h[:11]:>12}" for h in head)]
    for row in rows:
        if not row.get("ok"):
            lines.append("  " + f"{row['H']:>12.2f}" + f"{L['na_short']:>12}")
            continue
        cells = [f"{row['H']:.2f}", f"{row['L']:.2f}", str(row["n"]),
                 num(row["required_length"])]
        cells += [num(row[k], 3 if k == "eccentricity" else 2) for k, _ in CHECKS]
        cells.append(L["ok_short"] if row["status"] == "OK" else L["notok_short"])
        lines.append("  " + "".join(f"{c:>12}" for c in cells))
    return "\n".join(lines)


def verdict(study, L: dict) -> str:
    """Where along the range the design rule works."""
    ranges = study.ok_ranges()
    counted = [r for r in study.rows if r.get("ok")]
    if not ranges:
        return L["hs_none_ok"]
    if sum(1 for r in counted if r["status"] == "OK") == len(counted):
        return L["hs_all_ok"]
    spans = ", ".join(f"{lo:.2f} – {hi:.2f} m" if hi > lo else f"{lo:.2f} m"
                      for lo, hi in ranges)
    return L["hs_ranges"].format(spans=spans)


def table(study, L: dict) -> dict:
    """The height study as the interface's table."""
    from .summary import num
    columns = [L["hs_col_H"], L["hs_col_L"], L["hs_col_n"], L["hs_col_req"]] + \
        [L["chk_internal_sliding"] if k == "internal_sliding" else L[f"card_{k}"] for k, _ in CHECKS] + \
        [L["hs_col_status"]]
    rows = []
    for row in study.rows:
        if not row.get("ok"):
            rows.append({"cells": [f"{row['H']:.2f}"] + ["—"] * (len(columns) - 1),
                         "states": [""] * len(columns)})
            continue
        cells = [f"{row['H']:.2f}", f"{row['L']:.2f}", str(row["n"]), num(row["required_length"])]
        states = ["", "", "", "bad" if (not math.isfinite(row["required_length"])
                                        or max(row["required_length"], row["rule"]) > row["L"] + 1e-6)
                  else "ok"]
        for key, _ in CHECKS:
            cells.append(num(row[key], 3 if key == "eccentricity" else 2))
            m = row.get(f"m_{key}", math.nan)
            states.append("" if not math.isfinite(m) else ("ok" if m >= 1 - 1e-9 else "bad"))
        cells.append(L["ok_short"] if row["status"] == "OK" else L["notok_short"])
        states.append("ok" if row["status"] == "OK" else "bad")
        rows.append({"cells": cells, "states": states})
    return {"columns": columns, "rows": rows}
