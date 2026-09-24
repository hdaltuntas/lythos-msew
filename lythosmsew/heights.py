"""
The height study: the same design rule, run over a range of wall heights.

For every height the layout generator lays the reinforcement out by the rule
of the project (first layer, spacing, length as a share of the height or a
fixed length, type), the wall is analysed and the reinforcement length the
checks need is found. The result is a table, one row per height, of every
check's governing value and its margin — the value divided by what is
required, so that 1 is the limit whatever the check and whichever design
method is used — and the length needed.

It answers the questions a wall of varying height along its alignment asks:
up to which height the chosen reinforcement will do, and how long it has to
be at each height.
"""

from __future__ import annotations

import copy
import csv
import math
from typing import Callable, Dict, List, Optional

from .engine import MSEWall, MSEWError, generate_layers

__all__ = ["CHECKS", "HeightStudy", "margin", "to_csv", "to_xlsx"]

#: Checks followed over the heights: (key, where in the results)
CHECKS = [
    ("sliding", ("external", "sliding")),
    ("overturning", ("external", "overturning")),
    ("eccentricity", ("external", "eccentricity")),
    ("bearing", ("external", "bearing")),
    ("tensile", ("internal", "tensile")),
    ("pullout", ("internal", "pullout")),
    ("connection", ("internal", "connection")),
    ("internal_sliding", ("internal", "sliding")),
]


def margin(check: dict) -> float:
    """How far a check is from its limit: 1 at the limit, above 1 on the safe side."""
    if check is None or check.get("status") == "N/A":
        return float("nan")
    value, required = check["value"], check["required"]
    if check.get("kind") == "limit":
        return required / value if value > 0 else math.inf
    return value / required if required else value


def _get(res: dict, path) -> Optional[dict]:
    node = res
    for key in path:
        node = node.get(key) if isinstance(node, dict) else None
        if node is None:
            return None
    return node


class HeightStudy:
    """The design rule of one project, over a range of heights."""

    def __init__(self, config: dict, H_min: float, H_max: float, step: float):
        if step <= 0 or H_max < H_min or H_min <= 0:
            raise MSEWError("err_heights")
        self.config = copy.deepcopy(config)
        self.heights = []
        h = float(H_min)
        while h <= H_max + 1e-9 and len(self.heights) < 400:
            self.heights.append(round(h, 4))
            h += step
        self.rows: List[Dict] = []
        self.seismic = bool(config["seismic"]["enabled"])
        self.design = config["options"]["design"]

    def _wall(self, H: float) -> MSEWall:
        cfg = copy.deepcopy(self.config)
        lay = cfg["layout"]
        cfg["geometry"]["H"] = H
        cfg["geometry"]["embedment"] = min(cfg["geometry"]["embedment"], 0.5 * H)
        cfg["layers"] = generate_layers(H, lay["z1"], lay["Sv"], lay["rule"], lay["ratio"],
                                        lay["L"], lay["L_min"], lay["type"])
        return MSEWall(cfg)

    def run(self, progress: Optional[Callable[[int, int], None]] = None,
            is_cancelled: Optional[Callable[[], bool]] = None) -> "HeightStudy":
        self.rows = []
        total = len(self.heights)
        for index, H in enumerate(self.heights):
            if is_cancelled and is_cancelled():
                break
            row = {"H": H}
            try:
                wall = self._wall(H)
                res = wall.run()
                row.update(ok=True, L=wall.L, n=len(res["layers"]),
                           required_length=res["required_length"], rule=res["length_rule"])
                failed = False
                for key, path in CHECKS:
                    check = _get(res, path)
                    row[key] = check["value"] if check else float("nan")
                    row[f"m_{key}"] = margin(check)
                    failed = failed or (check is not None and check["status"] == "NOT OK")
                if res["seismic"]:
                    for key in ("sliding", "eccentricity", "bearing"):
                        check = res["seismic"]["external"][key]
                        row[f"m_seis_{key}"] = margin(check)
                        failed = failed or check["status"] == "NOT OK"
                    for key in ("tensile", "pullout", "connection"):
                        check = res["seismic"]["internal"][key]
                        row[f"m_seis_{key}"] = margin(check)
                        failed = failed or check["status"] == "NOT OK"
                row["status"] = "NOT OK" if failed else "OK"
            except MSEWError as exc:
                row.update(ok=False, status="N/A", error=exc.key)
            self.rows.append(row)
            if progress:
                progress(index + 1, total)
        return self

    def ok_ranges(self) -> List[tuple]:
        """The runs of consecutive heights at which every check holds, as (low, high)."""
        ranges, start, last = [], None, None
        for row in self.rows:
            if row.get("status") == "OK":
                start = row["H"] if start is None else start
                last = row["H"]
            elif start is not None:
                ranges.append((start, last))
                start = None
        if start is not None:
            ranges.append((start, last))
        return ranges


#: Columns of the exported table
COLUMNS = (["H", "L", "n", "required_length"] + [key for key, _ in CHECKS] + ["status"])


def to_csv(study: HeightStudy, path: str) -> str:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(COLUMNS)
        for row in study.rows:
            writer.writerow([row.get(c, "") for c in COLUMNS])
    return path


def to_xlsx(study: HeightStudy, path: str) -> str:
    try:
        import openpyxl
    except ImportError as exc:
        raise RuntimeError("openpyxl is not installed (pip install openpyxl).") from exc
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "heights"
    sheet.append(COLUMNS)
    for row in study.rows:
        values = []
        for c in COLUMNS:
            v = row.get(c, "")
            if isinstance(v, float) and not math.isfinite(v):
                v = ""
            values.append(v)
        sheet.append(values)
    book.save(path)
    return path
