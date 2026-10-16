"""Config-driven pipeline. Dumps every stage so the C model can be verified stage by stage.

Usage:
    python -m mini_isp.pipeline --input data/synth --config configs/default.yaml --out out/py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .modules import REGISTRY
from .raw_io import load_dng, load_raw, save_raw


def build(config: dict):
    stages = []
    for entry in config["pipeline"]:
        name = entry["module"]
        if name not in REGISTRY:
            raise KeyError(f"Module {name!r} not registered. Available: {sorted(REGISTRY)}")
        stages.append(REGISTRY[name](**entry.get("params", {})))
    return stages


def run(img, meta, stages, out_dir: Path | None = None):
    for i, stage in enumerate(stages, 1):
        img, meta = stage(img, meta)
        if out_dir is not None:
            save_raw(out_dir / f"{i:02d}_{stage.name}", img, meta)
    return img, meta


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, help="path to .raw/.json pair (no suffix needed) or .dng")
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default="out/py")
    a = ap.parse_args(argv)

    src = Path(a.input)
    img, meta = load_dng(src) if src.suffix.lower() == ".dng" else load_raw(src)
    config = yaml.safe_load(Path(a.config).read_text())
    stages = build(config)
    out_dir = Path(a.out)
    img, meta = run(img, meta, stages, out_dir)

    # Parameters the C model needs (firmware -> hardware hand-off).
    (out_dir / "params.json").write_text(json.dumps(meta, indent=2))
    print(f"[py] {len(stages)} stages -> {out_dir}  ({', '.join(s.name for s in stages)})")
    if "awb_gains" in meta:
        g = meta["awb_gains"]
        print(f"[py] AWB gains R={g['R']:.4f} G={g['G']:.4f} B={g['B']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
