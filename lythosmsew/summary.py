"""
Results as text, as summary cards and as tables.

Both the browser interface and the command line show the same thing: the
headline checks as a row of cards, the full account of the analysis as text,
and the layer-by-layer table. Assembling them here keeps that promise without
either side copying the other's wording, and it needs no interface toolkit at
all — pass a finished analysis and a language code.
"""

from __future__ import annotations

import math
from typing import List

from .i18n import TRANSLATIONS, warning_text

#: Card order, as the interface lays them out
CARD_KEYS = ["sliding", "overturning", "eccentricity", "bearing", "tensile", "pullout",
             "connection", "internal_sliding", "length"]

EXTERNAL = ["sliding", "overturning", "eccentricity", "bearing"]
INTERNAL = ["tensile", "pullout", "connection", "sliding"]


def _lang(lang: str) -> dict:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"])


def status_text(L: dict, status: str) -> tuple:
    """A check status as (short text, state) — state drives the card colour."""
    if status == "N/A":
        return L["na_short"], "na"
    return (L["ok_short"], "ok") if status == "OK" else (L["notok_short"], "bad")


def value_name(L: dict, design: str) -> str:
    """What a check's number is called: a factor of safety, or a capacity-demand ratio."""
    return L["value_CDR"] if design == "lrfd" else L["value_FS"]


def num(value, nd: int = 2) -> str:
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "∞" if value == math.inf else "—"
    return f"{value:,.{nd}f}"


def check_sub(L: dict, design: str, check: dict) -> str:
    """'FS = 2.31 ≥ 1.50' or 'e = 0.45 ≤ 0.90 m'."""
    if check["status"] == "N/A":
        return ""
    if check["kind"] == "limit":
        return f"e = {num(check['value'], 3)} ≤ {num(check['required'], 3)} m"
    return f"{value_name(L, design)} = {num(check['value'])} ≥ {num(check['required'])}"


def cards(analysis, lang: str = "en") -> List[dict]:
    """The headline numbers: every external check, every internal one, the length."""
    L = _lang(lang)
    res = analysis.results
    design = res["design"]
    out = []

    def card(key, check, sub_extra=""):
        text, state = status_text(L, check["status"])
        sub = check_sub(L, design, check)
        if sub_extra:
            sub = f"{sub} · {sub_extra}" if sub else sub_extra
        out.append({"key": key, "title": L[f"card_{key}"], "value": text, "sub": sub,
                    "state": state})

    for key in EXTERNAL:
        card(key, res["external"][key])
    for key in ("tensile", "pullout", "connection"):
        check = res["internal"][key]
        card(key, check, L["card_at_layer"].format(z=check["z"]) if math.isfinite(check["z"])
             else "")
    check = res["internal"]["sliding"]
    card("internal_sliding", check,
         L["card_at_layer"].format(z=check["z"]) if math.isfinite(check["z"]) else "")

    length = res["required_length"]
    shown = max(length, res["length_rule"]) if math.isfinite(length) else length
    out.append({"key": "length", "title": L["card_length"],
                "value": f"{shown:.2f} m" if math.isfinite(shown) else L["card_none"],
                "sub": L["card_length_sub"].format(rule=res["length_rule"]),
                "state": ("ok" if shown <= res["L"] + 1e-6 else "bad")
                if math.isfinite(shown) else "bad"})

    if res["seismic"]:
        checks = (list(res["seismic"]["external"].values())
                  + list(res["seismic"]["internal"].values()))
        counted = [c for c in checks if c["status"] != "N/A"]
        good = sum(c["status"] == "OK" for c in counted)
        state = "ok" if good == len(counted) else "bad"
        out.append({"key": "seismic", "title": L["card_seismic"],
                    "value": L["ok_short"] if state == "ok" else L["notok_short"],
                    "sub": L["card_seismic_sub"].format(n=good, total=len(counted)),
                    "state": state})
    return out


def layer_table(analysis, lang: str = "en", seismic: bool = False) -> dict:
    """The layer-by-layer table the interface shows under the cards."""
    L = _lang(lang)
    res = analysis.results
    if seismic and res["seismic"]:
        columns = [L["head_z"], L["head_Tmax"], L["head_Tmd"], L["head_Ttotal"], L["head_Pr"],
                   L["head_tensile"], L["head_pullout"], L["head_connection"]]
        rows = []
        for r in res["seismic"]["internal_rows"]:
            cells = [num(r["z"], 3), num(r["T_static"]), num(r["T_md"]), num(r["T_total"]),
                     num(r["P_r"])]
            states = ["", "", "", "", ""]
            for key in ("tensile", "pullout", "connection"):
                cells.append(num(r[key]["value"]))
                states.append("ok" if r[key]["status"] == "OK" else "bad")
            rows.append({"cells": cells, "states": states})
        return {"columns": columns, "rows": rows}

    columns = [L["head_z"], L["head_type"], L["col_L"], L["head_Sv"], L["head_Kr"],
               L["head_sigma_v"], L["head_Tmax"], L["head_Tlt"], L["head_La"], L["head_Le"],
               L["head_Fstar"], L["head_Pr"], L["head_tensile"], L["head_pullout"],
               L["head_connection"], L["head_sliding"]]
    rows = []
    for r in res["layers"]:
        tmax = r["T_design"] if res["design"] == "lrfd" else r["T_max"]
        cells = [num(r["z"], 3), r["type"], num(r["L"]), num(r["Sv"], 3), num(r["Kr"], 3),
                 num(r["sigma_v"], 1), num(tmax), num(r["T_lt"], 1), num(r["La"]),
                 num(r["Le"]), num(r["F_star"], 3), num(r["P_r"], 1)]
        states = [""] * len(cells)
        for key in INTERNAL:
            cells.append(num(r[key]["value"]))
            states.append("ok" if r[key]["status"] == "OK" else "bad")
        rows.append({"cells": cells, "states": states})
    return {"columns": columns, "rows": rows}


def bearing_table(analysis, lang: str = "en") -> dict:
    """Every bearing capacity method side by side."""
    L = _lang(lang)
    res = analysis.results
    b = res["bearing"]
    lrfd = res["design"] == "lrfd"
    columns = [L["head_method"], L["head_Nc"], L["head_Nq"], L["head_Ng"], L["head_qult"],
               L["head_qr"] if lrfd else L["head_qallow"], value_name(L, res["design"])]
    rows = []
    crit = analysis.crit
    sigma = b.get("sigma_v", math.nan)
    for key, entry in b["methods"].items():
        q = entry["q_ult"]
        if lrfd:
            allow = crit["phi_bearing"] * q
            value = allow / sigma if sigma > 0 else math.nan
            ok = value >= 1.0
        else:
            allow = q / crit["FS_bearing"]
            value = q / sigma if sigma > 0 else math.nan
            ok = value >= crit["FS_bearing"]
        rows.append({"cells": [L[f"method_{key}"], num(entry["N"]["Nc"]), num(entry["N"]["Nq"]),
                               num(entry["N"]["Ngamma"]), num(q, 1), num(allow, 1), num(value)],
                     "states": ["", "", "", "", "", "", "ok" if ok else "bad"],
                     "primary": key == b["primary"]})
    return {"columns": columns, "rows": rows}


def results_text(analysis, lang: str = "en") -> str:
    """The whole analysis as text, in the chosen language."""
    L = _lang(lang)
    w, res = analysis, analysis.results
    design = res["design"]
    lines = [L["res_title"], "-" * 96]
    lines.append(L["res_wall"].format(H=w.H, d=w.d, omega=w.omega, beta=w.beta, L=res["L"],
                                      n=len(res["layers"])))
    lines.append(L["res_design"].format(design=L[f"design_{design}"]))
    lines.append(L["res_ka"].format(kb=res["Ka"]["retained"], kr=res["Ka"]["reinforced"],
                                    theta=res["Ka"]["theta"]))
    f = res["forces"]
    lines.append(L["res_forces"].format(V=f["V"], Hf=f["H"], MR=f["M_R"], MO=f["M_O"], e=f["e"]))

    def block(title, checks, names, internal=False):
        lines.extend(["", title, "  " + L["res_check_head"].format(
            name="", value=L["res_value"], required=L["res_required"])])
        for key in names:
            check = checks[key]
            label = L["chk_internal_sliding"] if (internal and key == "sliding") else L[f"chk_{key}"]
            nd = 3 if check["kind"] == "limit" else 2
            lines.append("  " + L["res_check_line"].format(
                name=label[:26], value=num(check["value"], nd),
                required=num(check["required"], nd), status=status_text(L, check["status"])[0]))
            if internal and math.isfinite(check.get("z", math.nan)):
                lines.append("      " + L["res_governing"].format(z=check["z"]))

    block(L["res_external_title"] + f" ({value_name(L, design)})", res["external"], EXTERNAL)
    lines.append(L["res_sliding_plane"].format(plane=L[f"plane_{res['external']['sliding'].get('plane', 'reinforced')}"]))

    b = res["bearing"]
    lines += ["", L["res_bearing_title"]]
    if b["B_eff"] > 0:
        lines.append("  " + L["res_bearing"].format(B=b["B_eff"], s=b["sigma_v"], q=b["q_ult"],
                                                   method=L[f"method_{b['primary']}"]))
        table = bearing_table(analysis, lang)
        lines.append("  " + f"{table['columns'][0]:<24}"
                     + "".join(f"{c:>13}" for c in table["columns"][1:]))
        for row in table["rows"]:
            mark = " *" if row.get("primary") else ""
            cells = row["cells"]
            lines.append("  " + f"{(cells[0] + mark)[:24]:<24}"
                         + "".join(f"{c:>13}" for c in cells[1:]))

    block(L["res_internal_title"] + f" ({value_name(L, design)})", res["internal"], INTERNAL,
          internal=True)
    table = layer_table(analysis, lang)
    lines.append("")
    lines.append("  " + "".join(f"{c[:10]:>11}" for c in table["columns"]))
    for row in table["rows"]:
        lines.append("  " + "".join(f"{str(c)[:10]:>11}" for c in row["cells"]))

    if res["seismic"]:
        s = res["seismic"]
        lines += ["", L["res_seismic_title"],
                  "  " + L["res_seismic"].format(A=analysis.A, Am=s["Am"], PAE=s["PAE"],
                                                 PIR=s["PIR"], Pi=s["P_i"])]
        block("  " + L["res_external_title"], s["external"], EXTERNAL)
        block("  " + L["res_internal_title"], s["internal"], ["tensile", "pullout", "connection"],
              internal=True)

    length = res["required_length"]
    lines += ["", ("  " + L["res_length"].format(L=length, rule=res["length_rule"]))
              if math.isfinite(length) else ("  " + L["res_no_length"])]

    if res["warnings"]:
        lines += ["", L["warnings_title"]]
        lines += ["  • " + warning_text(lang, w) for w in res["warnings"]]
    return "\n".join(lines)


def warnings(analysis, lang: str = "en") -> List[str]:
    return [warning_text(lang, w) for w in analysis.results.get("warnings", [])]


def all_ok(res: dict) -> bool:
    checks = list(res["external"].values()) + list(res["internal"].values())
    if res["seismic"]:
        checks += list(res["seismic"]["external"].values())
        checks += list(res["seismic"]["internal"].values())
    return all(c["status"] != "NOT OK" for c in checks)


def headline(analysis, lang: str = "en") -> str:
    """One line for the status bar: the verdict, the weakest checks and the length."""
    L = _lang(lang)
    res = analysis.results
    ext, internal = res["external"], res["internal"]
    name = value_name(L, res["design"])
    verdict = L["ok_short"] if all_ok(res) else L["notok_short"]
    length = res["required_length"]
    tail = f" · L ≥ {max(length, res['length_rule']):.2f} m" if math.isfinite(length) else ""
    return (f"{verdict} · {L['chk_sliding']} {name} = {num(ext['sliding']['value'])} · "
            f"{L['chk_bearing']} {name} = {num(ext['bearing']['value'])} · "
            f"{L['chk_pullout']} {name} = {num(internal['pullout']['value'])}{tail}")
