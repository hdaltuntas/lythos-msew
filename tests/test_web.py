"""
Tests for the browser interface: the session that does the work, and the HTTP
layer that serves it. The server is started on a port of its own and driven
with urllib, so what is tested is the same thing the browser talks to.
"""
import json
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from lythosmsew import forms, render, summary
from lythosmsew.web import server as server_module
from lythosmsew.web.session import Session
from lythosmsew.web.strings import shell_strings

# --------------------------------------------------------------------------- #
#  The session
# --------------------------------------------------------------------------- #


def test_meta_carries_everything_the_page_needs():
    meta = Session().meta()
    assert meta["app"] == "Lythos MSEW"
    assert meta["languages"] == ["en", "tr"]
    assert meta["schema"]["wall"]["groups"]
    assert meta["defaults"]["H"] > 0
    assert meta["figures"] == render.PLOT_KEYS
    assert all(meta["figure_labels"][key] for key in meta["figures"])
    assert meta["height_views"] == render.HEIGHT_VIEWS


def test_analyse_returns_cards_text_tables_and_figures():
    result = Session().analyse(forms.defaults())
    assert result["ok"] and result["all_ok"]
    assert [card["key"] for card in result["cards"]] == summary.CARD_KEYS
    assert len(result["layers"]["rows"]) == 8
    assert len(result["bearing"]["rows"]) == 5
    assert sum(bool(row.get("primary")) for row in result["bearing"]["rows"]) == 1
    assert len(result["external"]["rows"]) == 4
    assert result["seismic_layers"] is None
    assert "seismic" not in result["figures"]


def test_the_earthquake_adds_its_table_card_and_figure():
    values = forms.defaults()
    values["seismic_enabled"] = True
    result = Session().analyse(values)
    assert result["seismic_layers"]["rows"]
    assert result["cards"][-1]["key"] == "seismic"
    assert "seismic" in result["figures"]
    assert len(result["external"]["columns"]) == 7


def test_a_wall_whose_resultant_leaves_the_base_still_reports():
    values = forms.defaults()
    values["layers"] = [{"z": 3.0, "L": 2.0, "type": "Strip 50x4"}]
    session = Session()
    result = session.analyse(values)
    assert not result["all_ok"]
    for key in result["figures"]:
        assert session.plot("analysis", key)[:4] == b"\x89PNG"


def test_a_refused_analysis_says_why_in_the_session_language():
    values = forms.defaults()
    values["H"] = 0.0
    session = Session(lang="tr")
    with pytest.raises(ValueError) as caught:
        session.analyse(values)
    assert "Duvar yüksekliği" in str(caught.value)


def test_the_layout_generator_fills_the_layer_table():
    values = forms.defaults()
    values["H"] = 9.0
    values["layout_type"] = "Geogrid 80"
    layers = Session().generate(values)["layers"]
    assert len(layers) == 12 and all(r["type"] == "Geogrid 80" for r in layers)
    assert layers[0]["L"] == pytest.approx(8.1)


def test_a_figure_needs_an_analysis_first():
    with pytest.raises(ValueError):
        Session().plot("analysis", "section")


def test_a_height_study_runs_in_the_background_and_can_be_read_back():
    session = Session()
    values = forms.defaults()
    values.update(H_min=4.0, H_max=8.0, H_step=1.0)
    assert session.start_heights(values)["ok"]
    for _ in range(400):
        if session.state()["job"] != "running":
            break
        time.sleep(0.05)
    payload = session.heights_payload()
    assert payload["ok"] and payload["n"] == 5
    assert session.plot("heights", "margins")[:4] == b"\x89PNG"
    assert session.plot("heights", "length")[:4] == b"\x89PNG"


def test_a_height_study_with_an_unknown_type_is_refused():
    values = forms.defaults()
    values["layout_type"] = "nothing"
    assert not Session().start_heights(values)["ok"]


def test_a_foreign_file_is_refused():
    with pytest.raises(ValueError):
        Session().load_project({"format": "lythos-bearing"})


def test_the_shell_has_every_string_in_both_languages():
    assert set(shell_strings("en")) == set(shell_strings("tr"))


# --------------------------------------------------------------------------- #
#  The HTTP layer
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def base_url():
    server_module.SESSION = Session()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server_module.Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def get(url):
    with urllib.request.urlopen(url) as response:
        return response.status, response.headers, response.read()


def post(url, payload):
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request) as response:
        return response.status, response.headers, response.read()


def test_the_page_and_its_files_are_served(base_url):
    for path, kind in (("/", "text/html"), ("/static/app.js", "javascript"),
                       ("/static/style.css", "text/css"), ("/favicon.ico", "svg")):
        status, headers, body = get(base_url + path)
        assert status == 200 and kind in headers["Content-Type"] and body


def test_the_static_route_cannot_leave_its_folder(base_url):
    with pytest.raises(urllib.error.HTTPError) as caught:
        get(base_url + "/static/../session.py")
    assert caught.value.code == 404


def test_analyse_plot_and_report_over_http(base_url):
    status, _, body = post(base_url + "/api/analyse", {"values": forms.defaults()})
    assert status == 200 and json.loads(body)["ok"]
    status, headers, body = get(base_url + "/api/plot?target=analysis&kind=section")
    assert headers["Content-Type"] == "image/png" and body[:4] == b"\x89PNG"
    status, headers, body = post(base_url + "/api/report", {"format": "pdf"})
    assert body[:5] == b"%PDF-"
    assert "lythosmsew_report.pdf" in headers["Content-Disposition"]


def test_an_unbounded_length_travels_as_null(base_url):
    values = forms.defaults()
    values.update(phi_f=0.0, c_f=5.0)                 # no length can save it
    _, _, body = post(base_url + "/api/analyse", {"values": values})
    data = json.loads(body)
    assert data["required_length"] is None


def test_the_layout_route(base_url):
    _, _, body = post(base_url + "/api/layout", {"values": forms.defaults()})
    assert len(json.loads(body)["layers"]) == 8


def test_a_saved_project_opens_again(base_url):
    values = forms.defaults()
    values["H"] = 7.5
    _, headers, body = post(base_url + "/api/project", {"values": values})
    assert "project.msew" in headers["Content-Disposition"]
    _, _, loaded = post(base_url + "/api/load", {"project": json.loads(body)})
    assert json.loads(loaded)["values"]["H"] == 7.5


def test_an_error_comes_back_as_json(base_url):
    values = forms.defaults()
    values["H"] = 0.0
    with pytest.raises(urllib.error.HTTPError) as caught:
        post(base_url + "/api/analyse", {"values": values})
    assert "error" in json.loads(caught.value.read())


def test_the_height_study_over_http(base_url):
    values = forms.defaults()
    values.update(H_min=5.0, H_max=6.0, H_step=1.0)
    _, _, body = post(base_url + "/api/heights", {"values": values})
    assert json.loads(body)["ok"]
    for _ in range(400):
        _, _, body = get(base_url + "/api/state")
        if json.loads(body)["job"] != "running":
            break
        time.sleep(0.05)
    _, _, body = get(base_url + "/api/heights")
    assert json.loads(body)["n"] == 2
    _, headers, body = post(base_url + "/api/export-heights", {"format": "xlsx"})
    assert "lythosmsew_heights.xlsx" in headers["Content-Disposition"] and body[:2] == b"PK"


def test_the_language_can_be_switched(base_url):
    _, _, body = post(base_url + "/api/language", {"lang": "tr"})
    assert json.loads(body)["strings"]["tab_inputs"].startswith("1 · Duvar")
    post(base_url + "/api/language", {"lang": "en"})
