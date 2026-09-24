"""The calculation report in all three formats, and the figures it carries."""
import copy
import zipfile

import pytest
from matplotlib.figure import Figure

from lythosmsew import render, report
from lythosmsew.config import DEFAULT_CONFIG
from lythosmsew.engine import MSEWall, generate_layers
from lythosmsew.heights import HeightStudy
from lythosmsew.plotting import PLOT_KEYS, Plotter, available_figures


@pytest.fixture(scope="module")
def wall():
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["seismic"]["enabled"] = True
    w = MSEWall(cfg)
    w.run()
    return w


@pytest.mark.parametrize("theme", ["light", "dark", "paper"])
def test_every_figure_draws_in_every_theme(wall, theme):
    for key in PLOT_KEYS:
        fig = Figure(figsize=(8, 6))
        Plotter(wall, "en", theme).draw(key, fig)
        assert fig.axes, key


def test_the_seismic_figure_is_offered_only_with_an_earthquake(wall):
    assert "seismic" in available_figures(wall)
    plain = MSEWall(DEFAULT_CONFIG)
    plain.run(with_length=False)
    assert "seismic" not in available_figures(plain)


def test_the_figures_come_out_as_png(wall):
    png = render.figure_to_png(render.analysis_figure(wall, "section", "tr"))
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_an_unknown_figure_is_refused(wall):
    with pytest.raises(ValueError):
        render.analysis_figure(wall, "nonsense")


def test_every_case_draws_its_figures():
    """The less common paths: geosynthetics, LRFD, a batter and a backslope, a strip
    load, a wall that fails."""
    grid = generate_layers(6.0, 0.3, 0.6, "ratio", 0.8, 0.0, 2.4, "Geotextile 60")
    cases = [
        {"layers": grid},
        {"options": {"design": "lrfd"}, "seismic": {"enabled": True}},
        {"geometry": {"batter": 12.0, "backslope": 15.0, "toe_slope": 10.0}},
        {"loads": {"strip_enabled": True, "strip_live": True}},
        {"soils": {"water_depth": 0.0}, "layers": [{"z": 3.0, "L": 2.0, "type": "Strip 50x4"}]},
    ]
    for changes in cases:
        cfg = copy.deepcopy(DEFAULT_CONFIG)
        for section, values in changes.items():
            if isinstance(values, dict):
                cfg[section].update(values)
            else:
                cfg[section] = values
        w = MSEWall(cfg)
        w.run()
        for key in available_figures(w):
            fig = Figure(figsize=(8, 6))
            Plotter(w, "en", "light").draw(key, fig)


def test_the_html_report_is_self_contained(wall, tmp_path):
    path = tmp_path / "r.html"
    report.export_html(str(path), wall, "en")
    text = path.read_text(encoding="utf-8")
    assert "data:image/png;base64," in text
    for words in ("External stability", "Bearing capacity of the foundation", "Pullout",
                  "Earthquake", "Method notes", "Vesić"):
        assert words in text


def test_the_turkish_report_is_in_turkish(wall, tmp_path):
    path = tmp_path / "r.html"
    report.export_html(str(path), wall, "tr")
    text = path.read_text(encoding="utf-8")
    assert "Dış duraylılık" in text and "Yöntem notları" in text and "Sıyrılma" in text


def test_the_pdf_report(wall, tmp_path):
    path = tmp_path / "r.pdf"
    report.export_pdf(str(path), wall, "tr")
    data = path.read_bytes()
    assert data[:5] == b"%PDF-" and len(data) > 50_000


def test_the_word_report(wall, tmp_path):
    path = tmp_path / "r.docx"
    report.export_docx(str(path), wall, "en")
    with zipfile.ZipFile(path) as archive:
        body = archive.read("word/document.xml").decode("utf-8")
    assert "Internal stability" in body


def test_the_height_study_reaches_the_report(wall):
    study = HeightStudy(DEFAULT_CONFIG, 5.0, 7.0, 1.0).run()
    text = report.build_html(wall, "en", {}, img_src=lambda k: k, heights=study)
    assert "Height study" in text and "Results by height" in text


def test_lrfd_speaks_of_capacity_demand_ratios():
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["options"]["design"] = "lrfd"
    w = MSEWall(cfg)
    w.run()
    text = report.build_html(w, "en", {}, img_src=lambda k: k)
    assert "CDR" in text and "φ bearing" in text
