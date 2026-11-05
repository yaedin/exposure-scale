"""Regenerate qr.svg and qr.png for the live site, locally.

Needs segno (pip install segno). Run from the repo root:
    python3 qr/make.py
"""
from pathlib import Path

import segno

URL = "https://yaedin.github.io/exposure-scale/"
HERE = Path(__file__).parent

# Error correction M keeps it at version 3 (big modules, scans from across a room); border=4 is the standard quiet zone.
qr = segno.make_qr(URL, error="m", boost_error=False)
style = dict(border=4, dark="#000", light="#fff")
qr.save(HERE / "qr.svg", scale=1, omitsize=True, xmldecl=False, svgclass=None, lineclass=None, **style)
qr.save(HERE / "qr.png", scale=54, **style)  # 1998 px wide, enough for print and slides
print(f"version {qr.version}, error {qr.error}, {qr.symbol_size(border=4)[0]} modules with quiet zone")
