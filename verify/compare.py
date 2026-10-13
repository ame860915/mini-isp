"""Stage-by-stage diff: Python float reference vs C fixed-point model.

For every stage dump present in both folders, report max/mean abs error and
exact-match rate, save an error heat map, and fail if a stage exceeds the
tolerance in the config's `verify:` section.

    python verify/compare.py --py out/py --c out/c --config configs/default.yaml
"""
import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_ref"))
from mini_isp.raw_io import load_raw  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--py", default="out/py")
ap.add_argument("--c", default="out/c")
ap.add_argument("--config", default="configs/default.yaml")
ap.add_argument("--report", default="out/verify")
a = ap.parse_args()

tol = yaml.safe_load(Path(a.config).read_text()).get("verify", {})
report = Path(a.report)
report.mkdir(parents=True, exist_ok=True)

rows, failed = [], False
for py_raw in sorted(Path(a.py).glob("[0-9][0-9]_*.raw")):
    stem = py_raw.with_suffix("")
    c_raw = Path(a.c) / py_raw.name
    if not c_raw.exists():
        rows.append((stem.name, "-", "-", "-", "-", "MISSING in C"))
        failed = True
        continue
    ref, _ = load_raw(stem)  # Python dump (already rounded to uint16 on save)
    dut, _ = load_raw(Path(a.c) / stem.name)
    err = dut.astype(np.int32) - ref.astype(np.int32)
    ae = np.abs(err)
    stage = stem.name.split("_", 1)[1]
    limit = tol.get(stage, {}).get("max_abs")
    ok = limit is None or ae.max() <= limit
    failed |= not ok
    rows.append((stem.name, int(ae.max()), f"{ae.mean():.4f}", f"{(ae == 0).mean() * 100:.2f}%",
                 "-" if limit is None else limit, "PASS" if ok else "FAIL"))

    fig, axs = plt.subplots(1, 2, figsize=(11, 3.6))
    im = axs[0].imshow(err, cmap="coolwarm", vmin=-max(1, ae.max()), vmax=max(1, ae.max()))
    axs[0].set_title(f"{stem.name}: C - Py (DN)")
    axs[0].axis("off")
    fig.colorbar(im, ax=axs[0], fraction=0.03)
    vals, counts = np.unique(err, return_counts=True)
    axs[1].bar(vals, counts)
    axs[1].set_yscale("log")
    axs[1].set_xlabel("error (DN)")
    axs[1].set_title("error histogram")
    fig.tight_layout()
    fig.savefig(report / f"{stem.name}_diff.png", dpi=100)
    plt.close(fig)

header = "| stage | max abs | mean abs | exact match | tol | result |\n|---|---|---|---|---|---|"
table = header + "\n" + "\n".join("| " + " | ".join(str(x) for x in r) + " |" for r in rows)
(report / "report.md").write_text(table + "\n")
print(table)
sys.exit(1 if failed else 0)
