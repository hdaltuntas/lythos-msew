"""
The analysis figures of Lythos MSEW.

Every figure is drawn on a Matplotlib `Figure` passed in by the caller, so the
same code serves the browser (PNG through `render`) and the report. Nothing
here needs a display.

    section      the wall to scale: foundation, reinforced and retained fill,
                 facing, every layer in its kind's colour, the failure surface,
                 the surcharges, the forces on the block and the bearing
                 pressure under it
    pressure     the horizontal stress down the wall, and the tension in each
                 layer beside the strength it may carry
    internal     every internal check of every layer as its margin over the
                 requirement
    pullout      the pullout resistance of each layer against its tension
    external     sliding, overturning, eccentricity and bearing as margins,
                 static and seismic side by side
    bearing      the bearing capacity of the foundation by every method beside
                 the pressure the wall puts on it
    length       the external and pullout margins against the reinforcement
                 length, the current and the required length marked
    seismic      the static and the dynamic tension in each layer against its
                 resistance (with an earthquake only)
"""

from __future__ import annotations

import math

import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Polygon, Rectangle
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter

from . import reinforcement as R
from .config import KIND_COLORS, METHOD_COLORS, PLOT_PALETTE, SOIL_FILL
from .i18n import TRANSLATIONS
from .plot_style import TITLE_FONT, label_box, style_axis, style_figure

#: The figures, in the order the interface offers them
PLOT_KEYS = ["section", "pressure", "internal", "pullout", "external", "bearing", "length",
             "seismic"]

#: Points of the length sweep
SWEEP_POINTS = 26

#: Colour of each check in the margin charts
CHECK_COLORS = {"sliding": PLOT_PALETTE["sliding"], "overturning": "#8C6BB1",
                "eccentricity": "#5E8C4A", "bearing": PLOT_PALETTE["demand"],
                "tensile": PLOT_PALETTE["tensile"], "pullout": PLOT_PALETTE["pullout"],
                "connection": PLOT_PALETTE["connection"],
                "internal_sliding": "#6B6A64"}


def margin(check: dict) -> float:
    """Value over required (required over value for a limit): 1 at the limit."""
    if check is None or check.get("status") == "N/A":
        return float("nan")
    value, required = check["value"], check["required"]
    if check.get("kind") == "limit":
        return required / value if value > 0 else math.inf
    return value / required if required else value


class Plotter:
    """Draws the figures of one finished `MSEWall`."""

    def __init__(self, wall, lang: str = "en", theme="light", titles: bool = True):
        self.w = wall
        self.res = wall.results
        self.lang = lang
        self.L = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        self.theme = theme
        self.titles = titles

    # ------------------------------------------------------------------ helpers
    def _fills(self):
        name = self.theme if isinstance(self.theme, str) else "light"
        return SOIL_FILL.get(name, SOIL_FILL["light"])

    def _title(self, fig, th, key: str, extra: str = "") -> None:
        if not self.titles:
            return
        text = self.L.get(f"fig_{key}", key)
        fig.suptitle(f"{text}{extra}", fontfamily=TITLE_FONT, fontsize=12.5, color=th["fg"])

    def _legend(self, ax, th, **kw) -> None:
        legend = ax.legend(fontsize=8, frameon=True, **kw)
        legend.get_frame().set_facecolor(th["panel"])
        legend.get_frame().set_edgecolor(th["border"])
        for text in legend.get_texts():
            text.set_color(th["fg"])

    def _value_name(self) -> str:
        return self.L["value_CDR"] if self.res["design"] == "lrfd" else self.L["value_FS"]

    def draw(self, key: str, fig: Figure) -> None:
        if key not in PLOT_KEYS:
            raise ValueError(f"unknown figure: {key}")
        getattr(self, f"_draw_{key}")(fig)

    # ------------------------------------------------------------------ section
    def _draw_section(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th, grid=False)
        w, res = self.w, self.res
        H, L = w.H, res["L"]
        tw, tb = math.tan(math.radians(w.omega)), math.tan(math.radians(w.beta))
        fills = self._fills()
        x_top = H * tw
        L_max = max(r["L"] for r in res["layers"])
        right = max(L_max + x_top, L) + max(0.6 * H, 2.0)
        left = -max(0.45 * H, 1.5)
        bottom = -max(0.45 * H, 1.5)

        # foundation, and the ground in front of the toe
        ax.add_patch(Rectangle((left, bottom), right - left, -bottom,
                               facecolor=fills["foundation"], edgecolor=th["border"],
                               linewidth=0.8, zorder=1))
        ts = math.tan(math.radians(w.toe_slope))
        front = [(left, 0.0), (0.0, 0.0), (0.0, w.d), (left, w.d + ts * left)]
        ax.add_patch(Polygon(front, closed=True, facecolor=fills["foundation"],
                             edgecolor=th["border"], linewidth=0.8, zorder=1))

        # retained and reinforced fill
        top_right = H + (right - x_top) * tb
        ax.add_patch(Polygon([(L, 0.0), (right, 0.0), (right, top_right),
                              (L + x_top, H + L * tb)], closed=True,
                             facecolor=fills["retained"], edgecolor=th["border"],
                             linewidth=0.8, zorder=1))
        ax.add_patch(Polygon([(0.0, 0.0), (L, 0.0), (L + x_top, H + L * tb), (x_top, H)],
                             closed=True, facecolor=fills["reinforced"],
                             edgecolor=th["border"], linewidth=0.9, zorder=2))

        # facing
        f = max(w.facing, 0.04 * H * 0.5)
        ax.add_patch(Polygon([(-f, 0.0), (0.0, 0.0), (x_top, H), (x_top - f, H)], closed=True,
                             facecolor=PLOT_PALETTE["facing"], edgecolor=th["fg_dim"],
                             linewidth=0.8, zorder=4))
        ax.add_patch(Rectangle((-f - 0.1, -0.15), f + 0.5, 0.15, facecolor=th["fg_dim"],
                               edgecolor="none", zorder=4))

        # the reinforcement
        seen = set()
        for r in res["layers"]:
            x0 = r["z"] * tw
            color = KIND_COLORS.get(r["kind"], th["fg"])
            label = None
            if r["type"] not in seen:
                seen.add(r["type"])
                label = r["type"]
            ax.plot([x0, x0 + r["L"]], [r["z"], r["z"]], color=color, linewidth=2.2,
                    solid_capstyle="butt", zorder=5, label=label)

        # failure surface(s)
        kinds = sorted({r["kind"] for r in res["layers"]}, key=R.is_extensible)
        drawn = set()
        for kind in kinds:
            family = R.is_extensible(kind)
            if family in drawn:
                continue
            drawn.add(family)
            zs = np.linspace(0.0, H, 60)
            xs = [w.failure_x(z, kind) for z in zs]
            ax.plot(xs, zs, color=PLOT_PALETTE["failure"], linewidth=1.4, linestyle="--",
                    zorder=6, label=self.L["plot_failure"] if len(drawn) == 1 else None)

        # water table
        if -w.dw > bottom:
            ax.axhline(-w.dw, color=PLOT_PALETTE["water"], linewidth=1.4, linestyle="--",
                       zorder=3)
            ax.text(right - 0.2, -w.dw, self.L["plot_water"], fontsize=8, ha="right",
                    va="bottom", color=PLOT_PALETTE["water"], zorder=6)

        # surcharges on the top
        q = w.q_dead + w.q_live
        arrow_h = 0.08 * H
        if q > 0:
            xs = np.linspace(x_top + 0.2, right - 0.3, 9)
            for x in xs:
                y = H + max(x - x_top, 0.0) * tb
                ax.annotate("", xy=(x, y), xytext=(x, y + arrow_h),
                            arrowprops=dict(arrowstyle="-|>", color=PLOT_PALETTE["surcharge"],
                                            lw=1.0), zorder=7)
            ax.text(xs[len(xs) // 2], H + (xs[len(xs) // 2] - x_top) * tb + arrow_h * 1.15,
                    f"q = {q:.1f} kPa", fontsize=8.5, ha="center", va="bottom",
                    color=th["fg"], bbox=label_box(th, 0.85), zorder=8)
        if w.strip_on:
            xc = x_top + w.strip_x
            y = H + max(w.strip_x, 0.0) * tb
            ax.add_patch(Rectangle((xc - w.strip_b / 2, y), w.strip_b, arrow_h * 0.5,
                                   facecolor=PLOT_PALETTE["demand"], edgecolor=th["fg_dim"],
                                   linewidth=0.6, zorder=8))
            ax.annotate(f"P = {w.strip_P:.0f} kN/m", xy=(xc, y + arrow_h * 0.5),
                        xytext=(xc, y + arrow_h * 2.2), ha="center", fontsize=8.5,
                        color=th["fg"], arrowprops=dict(arrowstyle="-|>",
                                                        color=PLOT_PALETTE["demand"], lw=1.4),
                        zorder=8)

        # forces on the block
        forces = res["forces"]
        h = forces["h"]
        thrust = next((fh for n, fh, _ in forces["horizontal"] if n == "F1"), 0.0)
        span = 0.22 * H
        xb = L + h / 3.0 * tw
        ax.annotate("", xy=(xb, h / 3.0), xytext=(xb + span, h / 3.0),
                    arrowprops=dict(arrowstyle="-|>", color=PLOT_PALETTE["thrust"], lw=2.0),
                    zorder=9)
        ax.text(xb + span, h / 3.0, f"  F₁ = {thrust:.0f} kN/m", fontsize=8.5, va="center",
                color=th["fg"], bbox=label_box(th, 0.85), zorder=9)
        v1 = next((v for n, v, _ in forces["vertical"] if n == "V1"), 0.0)
        xc, yc = L / 2.0 + x_top / 2.0, H / 2.0
        ax.annotate("", xy=(xc, yc - span / 2), xytext=(xc, yc + span / 2),
                    arrowprops=dict(arrowstyle="-|>", color=PLOT_PALETTE["weight"], lw=2.0),
                    zorder=9)
        ax.text(xc, yc + span / 2, f"V₁ = {v1:.0f} kN/m", fontsize=8.5, ha="center",
                va="bottom", color=th["fg"], bbox=label_box(th, 0.85), zorder=9)

        # the bearing pressure over the effective width
        b = res["bearing"]
        if b["B_eff"] > 0 and math.isfinite(b["sigma_v"]):
            depth = min(0.12 * H, 0.35 * -bottom)
            ax.add_patch(Rectangle((0.0, -depth), b["B_eff"], depth,
                                   facecolor=PLOT_PALETTE["pressure"], alpha=0.55,
                                   edgecolor=PLOT_PALETTE["sliding"], linewidth=0.9, zorder=3))
            ax.text(b["B_eff"] / 2.0, -depth / 2.0,
                    f"σv = {b['sigma_v']:.0f} kPa · B' = {b['B_eff']:.2f} m", fontsize=8,
                    ha="center", va="center", color=th["fg"], zorder=6)

        # dimensions
        ax.annotate("", xy=(left * 0.55, 0.0), xytext=(left * 0.55, H),
                    arrowprops=dict(arrowstyle="<->", color=th["fg_dim"], lw=0.9))
        ax.text(left * 0.55, H / 2.0, f" H = {H:.2f} m", fontsize=8.5, va="center",
                ha="right", rotation=90, color=th["fg"])
        ax.annotate("", xy=(0.0, bottom * 0.72), xytext=(L, bottom * 0.72),
                    arrowprops=dict(arrowstyle="<->", color=th["fg_dim"], lw=0.9))
        ax.text(L / 2.0, bottom * 0.72, f"L = {L:.2f} m", fontsize=8.5, ha="center",
                va="bottom", color=th["fg"])

        ax.set_xlim(left, right)
        ax.set_ylim(bottom, H + max(L * tb, 0) + 0.28 * H)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel(self.L["plot_x"])
        ax.set_ylabel(self.L["plot_y"])
        self._legend(ax, th, loc="upper left")
        self._title(fig, th, "section")

    # ------------------------------------------------------------------ pressure
    def _draw_pressure(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122, sharey=ax1)
        style_axis(ax1, th)
        style_axis(ax2, th)
        w, res = self.w, self.res
        H = w.H
        rows = res["layers"]
        ka = res["Ka"]["reinforced"]

        zs = np.linspace(0.0, H, 120)
        kind_at = lambda z: min(rows, key=lambda r: abs(r["z"] - z))["kind"]  # noqa: E731
        sh = [ka * R.kr_ratio(kind_at(z), H - z) * w.sigma_v(H - z) for z in zs]
        sa = [ka * w.sigma_v(H - z) for z in zs]
        ax1.plot(sh, zs, color=PLOT_PALETTE["demand"], linewidth=2.0,
                 label=self.L["plot_sigma_h"])
        ax1.plot(sa, zs, color=th["fg_dim"], linewidth=1.2, linestyle="--",
                 label=self.L["plot_Ka"])
        ax1.set_xlabel(self.L["plot_stress"])
        ax1.set_ylabel(self.L["plot_z"])
        ax1.set_ylim(0, H)
        ax1.set_xlim(left=0)
        self._legend(ax1, th, loc="upper right")

        z = [r["z"] for r in rows]
        lrfd = res["design"] == "lrfd"
        t = [r["T_design"] if lrfd else r["T_max"] for r in rows]
        allow = [r["tensile"]["capacity"] for r in rows]
        height = min(0.35 * min(r["Sv"] for r in rows), 0.3)
        ax2.barh(z, t, height=height, color=PLOT_PALETTE["demand"], alpha=0.85,
                 label=self.L["plot_Tmax"], zorder=3)
        ax2.plot(allow, z, marker="D", linestyle=":", color=PLOT_PALETTE["capacity"],
                 markersize=5, label=self.L["plot_Tallow"], zorder=4)
        ax2.set_xlabel(self.L["plot_force"])
        ax2.set_xlim(left=0)
        ax2.tick_params(labelleft=False)
        self._legend(ax2, th, loc="upper right")
        self._title(fig, th, "pressure")

    # ------------------------------------------------------------------ internal
    def _draw_internal(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        rows = self.res["layers"]
        z = np.array([r["z"] for r in rows])
        offsets = {"tensile": -0.09, "pullout": -0.03, "connection": 0.03, "sliding": 0.09}
        span = max(min(r["Sv"] for r in rows), 0.2)
        top = 1.0
        for key, off in offsets.items():
            m = np.array([margin(r[key]) for r in rows])
            top = max(top, np.nanmax(np.where(np.isfinite(m), m, np.nan)) if np.any(np.isfinite(m)) else 1.0)
            label = self.L[f"chk_{'internal_sliding' if key == 'sliding' else key}"]
            color = CHECK_COLORS["internal_sliding" if key == "sliding" else key]
            ax.scatter(m, z + off * span, s=34, color=color, edgecolor=th["panel"],
                       linewidth=0.8, label=label, zorder=4)
            ax.plot(m, z + off * span, color=color, linewidth=0.8, alpha=0.5, zorder=3)
        ax.axvline(1.0, color=PLOT_PALETTE["required"], linewidth=1.4, linestyle="--",
                   label=self.L["plot_limit"], zorder=2)
        ax.set_xscale("log")
        hi = max(top * 1.3, 3.0)
        ax.set_xlim(0.3, hi)
        ticks = [t for t in (0.3, 0.5, 0.7, 1, 1.5, 2, 3, 5, 7, 10, 20, 50, 100) if t <= hi]
        ax.xaxis.set_major_locator(FixedLocator(ticks))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_ylim(0, self.w.H)
        ax.set_xlabel(f"{self._value_name()} / {self.L['res_required']}")
        ax.set_ylabel(self.L["plot_z"])
        self._legend(ax, th, loc="lower right")
        self._title(fig, th, "internal")

    # ------------------------------------------------------------------ pullout
    def _draw_pullout(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        rows = self.res["layers"]
        lrfd = self.res["design"] == "lrfd"
        z = [r["z"] for r in rows]
        ax.plot([r["P_r"] for r in rows], z, marker="o", color=PLOT_PALETTE["pullout"],
                linewidth=1.8, label=self.L["plot_Pr"], zorder=4)
        ax.plot([r["pullout"]["capacity"] for r in rows], z, marker="o", linestyle=":",
                color=PLOT_PALETTE["capacity"], linewidth=1.2,
                label=("φ·Pr" if lrfd else f"Pr / {self.L['value_FS']}"), zorder=4)
        ax.plot([r["T_design"] if lrfd else r["T_max"] for r in rows], z, marker="s",
                color=PLOT_PALETTE["demand"], linewidth=1.8, label=self.L["plot_Tmax"],
                zorder=4)
        for r in rows:
            if not r["pullout"]["Le_ok"]:
                ax.annotate(f"Le = {r['Le']:.2f} m", xy=(r["P_r"], r["z"]), xytext=(8, 0),
                            textcoords="offset points", fontsize=8, color=PLOT_PALETTE["bad"])
        ax.set_xlabel(self.L["plot_force"])
        ax.set_ylabel(self.L["plot_z"])
        ax.set_xlim(left=0)
        ax.set_ylim(0, self.w.H)
        self._legend(ax, th, loc="upper right")
        self._title(fig, th, "pullout")

    # ------------------------------------------------------------------ external
    def _draw_external(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th, axis="y")
        keys = ["sliding", "overturning", "eccentricity", "bearing"]
        sets = [(self.L["plot_static"], self.res["external"], PLOT_PALETTE["capacity"])]
        if self.res["seismic"]:
            sets.append((self.L["plot_seismic"], self.res["seismic"]["external"],
                         PLOT_PALETTE["seismic"]))
        width = 0.8 / len(sets)
        x = np.arange(len(keys))
        top = 1.0
        for i, (label, checks, color) in enumerate(sets):
            m = [margin(checks[k]) for k in keys]
            shown = [v if math.isfinite(v) else 0.0 for v in m]
            bars = ax.bar(x + (i - (len(sets) - 1) / 2) * width, shown, width * 0.92,
                          color=color, label=label, zorder=3)
            for bar, value, key in zip(bars, m, keys):
                check = checks[key]
                if check["status"] == "N/A":
                    text = self.L["na_short"]
                elif check["kind"] == "limit":
                    text = f"e = {check['value']:.2f}"
                else:
                    text = f"{check['value']:.2f}"
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), text,
                        ha="center", va="bottom", fontsize=8, color=th["fg"])
                if math.isfinite(value):
                    top = max(top, value)
        ax.axhline(1.0, color=PLOT_PALETTE["required"], linewidth=1.4, linestyle="--",
                   label=self.L["plot_limit"], zorder=4)
        ax.set_xticks(x)
        ax.set_xticklabels([self.L[f"card_{k}"] for k in keys])
        ax.set_ylabel(self.L["plot_margin"])
        ax.set_ylim(0, top * 1.18)
        self._legend(ax, th, loc="upper right")
        self._title(fig, th, "external", f" ({self._value_name()})")

    # ------------------------------------------------------------------ bearing
    def _draw_bearing(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th, axis="x")
        b = self.res["bearing"]
        lrfd = self.res["design"] == "lrfd"
        crit = self.w.crit
        keys = list(b["methods"])
        if not keys:
            # the resultant leaves the base: there is no effective width to bear on
            ax.text(0.5, 0.5, f"B' = L − 2e = {b['B_eff']:.2f} m ≤ 0", transform=ax.transAxes,
                    ha="center", va="center", fontsize=12, color=PLOT_PALETTE["bad"])
            ax.set_xticks([])
            ax.set_yticks([])
            self._title(fig, th, "bearing")
            return
        y = np.arange(len(keys))
        ult = [b["methods"][k]["q_ult"] for k in keys]
        allow = [(crit["phi_bearing"] * q) if lrfd else q / crit["FS_bearing"] for q in ult]
        ax.barh(y + 0.2, ult, 0.38, color=[METHOD_COLORS.get(k, th["fg_dim"]) for k in keys],
                label=self.L["plot_ultimate"], zorder=3)
        ax.barh(y - 0.2, allow, 0.38, color=[METHOD_COLORS.get(k, th["fg_dim"]) for k in keys],
                alpha=0.45, label=self.L["plot_resist" if lrfd else "plot_allow"], zorder=3)
        for i, (q, a) in enumerate(zip(ult, allow)):
            ax.text(q, i + 0.2, f" {q:,.0f}", va="center", fontsize=8, color=th["fg"])
            ax.text(a, i - 0.2, f" {a:,.0f}", va="center", fontsize=8, color=th["fg_dim"])
        if math.isfinite(b.get("sigma_v", math.nan)):
            ax.axvline(b["sigma_v"], color=PLOT_PALETTE["applied"], linewidth=1.8,
                       linestyle="--", label=f"{self.L['plot_applied']} = {b['sigma_v']:.0f} kPa",
                       zorder=4)
        ax.set_yticks(y)
        ax.set_yticklabels([self.L[f"method_{k}"] + (" *" if k == b["primary"] else "")
                            for k in keys])
        ax.set_xlabel(self.L["plot_pressure"])
        sigma = b.get("sigma_v", 0.0)
        ax.set_xlim(0, max(ult + [sigma if math.isfinite(sigma) else 0.0]) * 1.18)
        self._legend(ax, th, loc="lower right")
        self._title(fig, th, "bearing")

    # ------------------------------------------------------------------ length
    def length_sweep(self):
        """Margins of the external checks and the weakest pullout over a range of L."""
        w = self.w
        req = self.res["required_length"]
        hi = max(1.6 * w.H, self.res["L"] * 1.3, req * 1.2 if math.isfinite(req) else 0)
        lengths = np.linspace(0.35 * w.H, hi, SWEEP_POINTS)
        keys = ["sliding", "overturning", "eccentricity", "bearing", "pullout"]
        if self.res["seismic"]:
            keys.append("seismic")
        out = {k: [] for k in keys}
        for length in lengths:
            try:
                res = w.with_length(length).run(with_length=False)
            except ValueError:
                for k in out:
                    out[k].append(float("nan"))
                continue
            for k in ("sliding", "overturning", "eccentricity", "bearing"):
                out[k].append(margin(res["external"][k]))
            out["pullout"].append(min(margin(r["pullout"]) if r["pullout"]["Le_ok"] else 0.0
                                      for r in res["layers"]))
            if res["seismic"]:
                checks = list(res["seismic"]["external"].values())
                checks += [r["pullout"] for r in res["seismic"]["internal_rows"]]
                out["seismic"].append(min(margin(c) if c.get("Le_ok", True) else 0.0
                                          for c in checks if c["status"] != "N/A"))
        return lengths, out

    def _draw_length(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        lengths, out = self.length_sweep()
        top = 1.5
        for key, values in out.items():
            values = np.array(values, dtype=float)
            if not np.any(np.isfinite(values)):
                continue
            if key == "seismic":
                ax.plot(lengths, values, color=PLOT_PALETTE["seismic"], linewidth=1.6,
                        linestyle="--", label=self.L["plot_seismic_weakest"])
            else:
                ax.plot(lengths, values, color=CHECK_COLORS[key], linewidth=1.9,
                        label=self.L[f"card_{key}"])
            finite = values[np.isfinite(values)]
            if finite.size:
                top = max(top, min(float(np.max(finite)), 6.0))
        ax.axhline(1.0, color=PLOT_PALETTE["required"], linewidth=1.3, linestyle="--",
                   label=self.L["plot_limit"])
        ax.axvline(self.res["L"], color=th["fg_dim"], linewidth=1.2, linestyle=":",
                   label=f"{self.L['plot_current']} = {self.res['L']:.2f} m")
        req = self.res["required_length"]
        if math.isfinite(req):
            ax.axvline(req, color=th["fg"], linewidth=1.4, linestyle="-.",
                       label=f"{self.L['plot_required']} = {req:.2f} m")
        ax.set_ylim(0, top * 1.1)
        ax.set_xlim(lengths[0], lengths[-1])
        ax.set_xlabel(self.L["plot_length"])
        ax.set_ylabel(self.L["plot_margin"])
        self._legend(ax, th, loc="upper left")
        self._title(fig, th, "length")

    # ------------------------------------------------------------------ seismic
    def _draw_seismic(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        s = self.res["seismic"]
        if not s:
            ax.text(0.5, 0.5, "—", transform=ax.transAxes, ha="center", color=th["fg_dim"])
            return
        rows = s["internal_rows"]
        z = [r["z"] for r in rows]
        ax.plot([r["T_static"] for r in rows], z, marker="s", color=PLOT_PALETTE["demand"],
                linewidth=1.4, linestyle=":", label=self.L["plot_Tmax"])
        ax.plot([r["T_total"] for r in rows], z, marker="s", color=PLOT_PALETTE["seismic"],
                linewidth=1.9, label=self.L["plot_Ttotal"])
        ax.plot([r["pullout"]["capacity"] for r in rows], z, marker="o",
                color=PLOT_PALETTE["pullout"], linewidth=1.6, label=self.L["plot_Pr"])
        ax.plot([r["tensile"]["capacity"] for r in rows], z, marker="D",
                color=PLOT_PALETTE["capacity"], linewidth=1.2, linestyle="--",
                label=self.L["plot_Tallow"])
        ax.set_xscale("symlog", linthresh=10.0)
        ax.set_xlabel(self.L["plot_force"])
        ax.set_ylabel(self.L["plot_z"])
        ax.set_ylim(0, self.w.H)
        ax.set_xlim(left=0)
        self._legend(ax, th, loc="upper right")
        self._title(fig, th, "seismic", f" — Am = {s['Am']:.3f}")


def available_figures(wall=None) -> list:
    """The figures that apply: the seismic one only with an earthquake."""
    keys = list(PLOT_KEYS)
    if wall is None or not wall.results.get("seismic"):
        keys.remove("seismic")
    return keys
