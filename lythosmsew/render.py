"""
Figure production for Lythos MSEW.

The interface runs in a browser, so figures are drawn on the server and sent
as PNG. The same functions draw the figures that go into the report, so what
is on screen and what is in the report are the same picture.

Matplotlib is used through the Agg backend: the server needs no display.
"""

from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")

from matplotlib.figure import Figure  # noqa: E402

from . import height_plots  # noqa: E402
from .i18n import TRANSLATIONS  # noqa: E402
from .plotting import PLOT_KEYS, Plotter, available_figures  # noqa: E402

#: Resolution of the PNGs (enough for the screen, and used by the report)
DPI = 130

#: The height study figures
HEIGHT_VIEWS = list(height_plots.VIEWS)

__all__ = ["DPI", "PLOT_KEYS", "HEIGHT_VIEWS", "figure_to_png", "analysis_figure",
           "height_figure", "available_figures"]


def figure_to_png(fig: Figure, dpi: int = DPI) -> bytes:
    """The figure as PNG bytes."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    return buf.getvalue()


def analysis_figure(wall, key: str, lang: str = "en", theme: str = "light",
                    size=(10.0, 7.0)) -> Figure:
    """One analysis figure."""
    if key not in PLOT_KEYS:
        raise ValueError(f"unknown figure: {key}")
    fig = Figure(figsize=size, dpi=DPI)
    Plotter(wall, lang, theme).draw(key, fig)
    return fig


def height_figure(study, view: str, lang: str = "en", theme: str = "light",
                  size=(10.0, 7.0), titles: bool = True) -> Figure:
    """One height study figure."""
    if view not in HEIGHT_VIEWS:
        raise ValueError(f"unknown height study view: {view}")
    L = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    fig = Figure(figsize=size, dpi=DPI)
    {"margins": height_plots.plot_margins,
     "length": height_plots.plot_length}[view](fig, study, L, theme=theme, titles=titles)
    return fig
