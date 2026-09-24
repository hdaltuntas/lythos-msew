"""The height study: one design per height, the verdict and the exports."""
import copy
import csv
import math

import pytest

from lythosmsew import height_plots
from lythosmsew.config import DEFAULT_CONFIG
from lythosmsew.engine import MSEWError
from lythosmsew.heights import CHECKS, HeightStudy, margin
from lythosmsew.i18n import TRANSLATIONS


@pytest.fixture(scope="module")
def study():
    return HeightStudy(DEFAULT_CONFIG, 3.0, 9.0, 1.0).run()


def test_every_height_is_designed(study):
    assert [row["H"] for row in study.rows] == [3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
    for row in study.rows:
        assert row["ok"]
        assert row["L"] == pytest.approx(max(0.9 * row["H"], 2.4))
        for key, _ in CHECKS:
            assert key in row and f"m_{key}" in row


def test_the_six_metre_wall_is_the_project(study):
    row = next(r for r in study.rows if r["H"] == 6.0)
    assert row["n"] == 8 and row["status"] == "OK"


def test_the_ranges_where_the_rule_works(study):
    ranges = study.ok_ranges()
    assert ranges and ranges[-1][1] == 9.0
    text = height_plots.verdict(study, TRANSLATIONS["en"])
    assert "Every check holds" in text


def test_a_margin_is_one_at_the_limit():
    assert margin({"value": 1.5, "required": 1.5, "kind": "ratio", "status": "OK"}) == 1.0
    assert margin({"value": 0.5, "required": 1.0, "kind": "limit", "status": "OK"}) == 2.0
    assert math.isnan(margin({"status": "N/A", "value": 0, "required": 0}))


def test_a_bad_range_is_refused():
    with pytest.raises(MSEWError):
        HeightStudy(DEFAULT_CONFIG, 5.0, 3.0, 1.0)


def test_the_seismic_margins_are_followed():
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["seismic"]["enabled"] = True
    study = HeightStudy(cfg, 6.0, 7.0, 1.0).run()
    assert all("m_seis_pullout" in row for row in study.rows)


def test_the_exports(study, tmp_path):
    from lythosmsew.heights import to_csv, to_xlsx
    path = to_csv(study, str(tmp_path / "h.csv"))
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert rows[0][0] == "H" and len(rows) == 8
    import openpyxl
    book = openpyxl.load_workbook(to_xlsx(study, str(tmp_path / "h.xlsx")))
    assert book.active.max_row == 8


def test_the_text_and_the_table_in_both_languages(study):
    for lang in ("en", "tr"):
        L = TRANSLATIONS[lang]
        assert L["hs_title"] in height_plots.summary_text(study, L)
        table = height_plots.table(study, L)
        assert len(table["rows"]) == len(study.rows)
        assert all(len(r["cells"]) == len(table["columns"]) for r in table["rows"])
