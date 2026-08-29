#!/usr/bin/env python3
"""
emit_forecaster_engine.py  (v1.0.0)

Emit the forecast-engine constants as a small, hash-gated JSON feed so the
Well Logger app can consume them live (raw.githubusercontent) instead of
carrying a baked copy that drifts.

The feed is the *engine subset* of the 11b DATA bundle — the fields the
forecast maths actually reads — with the heavy DEM base_layer excluded:

    cluster_coeffs, block_tf, P_clim, PET_clim, winter_climatology_mm, wells

Hash-gating: the file is rewritten ONLY when the content hash of that subset
changes. Script 11b runs at least weekly during active work, but while the
SSM is stable the subset is byte-identical run to run, so no-op runs produce
no new commit and `last_changed` honestly reflects when the forecast basis
last moved. That is the granularity the monthly "has it changed?" check wants
— the engine subset, not all of 11b's (cosmetically churny) output.

Hook in 11b (build_forecaster_html, just after the bundle is built):

    from emit_forecaster_engine import emit_engine
    bundle = _build_forecaster_data_bundle()
    emit_engine(bundle)                       # <-- add this line

Bootstrap / verify from an already-rendered forecaster.html (path or URL):

    python living/emit_forecaster_engine.py --from-html \
      https://raw.githubusercontent.com/newbroman/Newborough_Hydrology/main/outputs/11b_spatial_thresholds/forecaster.html
"""
from __future__ import annotations
import json
import hashlib
import datetime
from pathlib import Path

ENGINE_KEYS = ("cluster_coeffs", "block_tf", "P_clim",
               "PET_clim", "winter_climatology_mm", "wells")
SCHEMA = "nw-engine-1"
DEFAULT_OUT = Path(__file__).resolve().parent / "forecaster_engine.json"


def _engine_subset(bundle: dict) -> dict:
    return {k: bundle[k] for k in ENGINE_KEYS if k in bundle}


def _hash(subset: dict) -> str:
    canon = json.dumps(subset, sort_keys=True, separators=(",", ":"),
                       default=str).encode("utf-8")
    return hashlib.sha256(canon).hexdigest()[:16]


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def emit_engine(bundle: dict, out_path: Path | str | None = None) -> Path:
    """Write the engine feed, gated on the engine-subset content hash.

    Returns the output path. Prints a one-line console note (unchanged /
    written) so the weekly pipeline log shows when the basis last moved.
    """
    out = Path(out_path) if out_path else DEFAULT_OUT
    subset = _engine_subset(bundle)
    h = _hash(subset)

    prev_changed = None
    if out.exists():
        try:
            prev = json.loads(out.read_text(encoding="utf-8"))
            if prev.get("hash") == h:
                print(f"[emit_forecaster_engine] engine constants unchanged "
                      f"since {prev.get('last_changed', '?')} (hash {h}); no rewrite.")
                return out
            prev_changed = prev.get("last_changed")
        except Exception:
            pass  # unreadable prior -> treat as changed

    now = _now()
    payload = {
        "generated": now,
        "last_changed": now,           # hash moved -> this IS the change time
        "hash": h,
        "schema": SCHEMA,
        "source": "11b_spatial_thresholds DATA (base_layer excluded)",
    }
    payload.update(subset)
    out.write_text(json.dumps(payload, indent=1, default=str), encoding="utf-8")
    if prev_changed:
        print(f"[emit_forecaster_engine] engine constants CHANGED "
              f"(was {prev_changed}); wrote {out.name} (hash {h}).")
    else:
        print(f"[emit_forecaster_engine] wrote {out.name} (hash {h}).")
    return out


def _bundle_from_html(text: str) -> dict:
    """Extract the injected `const DATA = {...};` object from a rendered page."""
    import re
    m = re.search(r"(?:const|let|var)\s+DATA\s*=\s*", text)
    if not m:
        raise ValueError("no `DATA =` assignment found")
    i = text.index("{", m.end())
    depth, j = 0, i
    while j < len(text):
        c = text[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    return json.loads(text[i:j + 1])


if __name__ == "__main__":
    import argparse
    import urllib.request
    ap = argparse.ArgumentParser(description="Emit / verify the forecaster engine feed.")
    ap.add_argument("--from-html", metavar="PATH_OR_URL",
                    help="Bootstrap the feed from an already-rendered forecaster.html")
    ap.add_argument("--out", default=None, help="Output path (default living/forecaster_engine.json)")
    args = ap.parse_args()
    if args.from_html:
        src = args.from_html
        if src.startswith("http"):
            text = urllib.request.urlopen(src, timeout=60).read().decode("utf-8", "replace")
        else:
            text = Path(src).read_text(encoding="utf-8")
        emit_engine(_bundle_from_html(text), args.out)
    else:
        ap.error("nothing to do: pass --from-html for standalone use, "
                 "or import emit_engine() from Script 11b.")
