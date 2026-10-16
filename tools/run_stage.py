"""Run ONE Python reference stage on ONE input and save the result.

    python tools/run_stage.py --stage blc --input data/synth        --out out/step/01_blc
    python tools/run_stage.py --stage awb --input out/step/01_blc   --out out/step/02_awb
    python tools/run_stage.py --stage awb --input out/step/01_blc   --out out/step/02_awb_manual \
        --params '{"method": "manual", "gains": {"R": 1.8, "G": 1.0, "B": 1.4}}'

Input/output are .raw/.json pairs (give the path without suffix).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_ref"))
from mini_isp.modules import REGISTRY
from mini_isp.raw_io import load_raw, save_raw

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--stage", required=True, choices=sorted(REGISTRY))
ap.add_argument("--input", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--params", default="{}", help="JSON dict of module params")
a = ap.parse_args()

img, meta = load_raw(a.input)
module = REGISTRY[a.stage](**json.loads(a.params))
out, meta_out = module(img, meta)
save_raw(a.out, out, meta_out)

print(f"[{a.stage}] {module}  {a.input} -> {a.out}.raw")
changed = {k: meta_out[k] for k in meta_out if k != "gt" and meta.get(k) != meta_out[k]}
print(f"[{a.stage}] meta changed: {json.dumps(changed)}")
