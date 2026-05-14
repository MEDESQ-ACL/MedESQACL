\
from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def _col_to_idx(ref: str) -> int:
    letters = "".join(ch for ch in ref if ch.isalpha())
    idx = 0
    for ch in letters:
        idx = idx * 26 + ord(ch.upper()) - 64
    return idx - 1


def _read_shared_strings(zf: zipfile.ZipFile):
    try:
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    out = []
    for si in root.findall("main:si", NS):
        out.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["main"])))
    return out


def _read_workbook_map(zf: zipfile.ZipFile):
    wbroot = ET.fromstring(zf.read("xl/workbook.xml"))
    relroot = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rels = {rel.attrib["Id"]: rel.attrib["Target"] for rel in relroot.findall("pkgrel:Relationship", NS)}
    sheets = {}
    for sh in wbroot.findall(".//main:sheet", NS):
        rid = sh.attrib["{%s}id" % NS["rel"]]
        target = rels[rid]
        if not target.startswith("xl/"):
            target = "xl/" + target
        sheets[sh.attrib["name"].strip()] = target
    return sheets


def _cell_value(cell, shared):
    t = cell.attrib.get("t")
    if t == "inlineStr":
        return "".join(e.text or "" for e in cell.iter("{%s}t" % NS["main"]))
    v = cell.find("main:v", NS)
    if v is None:
        return None
    raw = v.text or ""
    if t == "s":
        try:
            return shared[int(raw)]
        except Exception:
            return raw
    if t == "b":
        return raw == "1"
    if re.fullmatch(r"-?\d+", raw):
        try:
            return int(raw)
        except Exception:
            return raw
    if re.fullmatch(r"-?\d+\.\d+(?:E[+-]?\d+)?", raw, flags=re.I):
        try:
            return float(raw)
        except Exception:
            return raw
    return raw


def _read_sheet_rows(zf: zipfile.ZipFile, target: str, shared):
    root = ET.fromstring(zf.read(target))
    rows = []
    max_col = -1
    for row in root.findall("main:sheetData/main:row", NS):
        values = []
        for cell in row.findall("main:c", NS):
            idx = _col_to_idx(cell.attrib.get("r", "A1"))
            while len(values) <= idx:
                values.append(None)
            values[idx] = _cell_value(cell, shared)
            max_col = max(max_col, idx)
        rows.append(values)
    if max_col < 0:
        return rows
    for values in rows:
        values.extend([None] * (max_col + 1 - len(values)))
    return rows


def read_xlsx_sheets(path: str | Path) -> dict[str, list[list[object]]]:
    """Read XLSX sheets using only the Python standard library.

    The function intentionally avoids spreadsheet metadata and does not preserve styles.
    It is suitable for reproducible extraction of template rows from the source workbook.
    """
    path = Path(path)
    with zipfile.ZipFile(path) as zf:
        shared = _read_shared_strings(zf)
        mapping = _read_workbook_map(zf)
        return {name: _read_sheet_rows(zf, target, shared) for name, target in mapping.items()}
