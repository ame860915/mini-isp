# mini-isp

RAW-to-RGB image signal processor built two ways:

* **`python_ref/`**: floating-point reference model (readable, config-driven)
* **`c_model/`**: fixed-point C model (integer-only, hardware-style)

The two are **verified stage by stage**: every stage dumps its output, and `verify/` reports the
bit-level difference against a per-stage tolerance. CI fails if any stage drifts.

![stages](docs/img/stages.png)

## Status

| # | Stage | Python ref | C fixed-point | Verified (max abs err) | Notes |
|---|---|---|---|---|---|
| 1 | Black level correction | ✅ | ✅ | 0 DN (bit-exact) | [docs/01_blc.md](docs/01_blc.md) |
| 2 | White balance (gray world) | ✅ | ✅ Q3.10 gains | ≤ 1 DN | [docs/02_awb.md](docs/02_awb.md) |
| 3 | Defect pixel correction | ⬜ | ⬜ | | |
| 4 | Demosaic (bilinear → Malvar-He-Cutler) | ⬜ | ⬜ | | |
| 5 | Color correction matrix | ⬜ | ⬜ | | |
| 6 | Gamma / tone curve (LUT) | ⬜ | ⬜ | | |

IQ metrics: PSNR ✅ · SSIM ⬜ · ΔE2000 ⬜ · slanted-edge MTF ⬜

## Quick start

```bash
pip install numpy pyyaml matplotlib pytest   # + rawpy for real DNG input
make test       # unit tests
make verify     # synthetic RAW -> Python ref -> C model -> stage-by-stage diff
make preview    # quick-look PNG of each stage
```

Example `make verify` output:

```
| stage  | max abs | mean abs | exact match | tol | result |
|--------|---------|----------|-------------|-----|--------|
| 01_blc | 0       | 0.0000   | 100.00%     | 0   | PASS   |
| 02_awb | 1       | 0.0702   | 92.98%      | 3   | PASS   |
```

## Design

```
            ┌──────────── Python float reference ────────────┐
RAW ──────► │ BLC → AWB → DPC → Demosaic → CCM → Gamma → ... │ ──► stage dumps (out/py)
 │          └──────────────────────┬──────────────────────────┘
 │                                 │ params (AWB gains, ...)  = firmware → hardware hand-off
 │          ┌──────────── C fixed-point model ───────────────┐
 └────────► │ same stages, integer arithmetic                │ ──► stage dumps (out/c)
            └────────────────────────────────────────────────┘
                                   ▼
                        verify/compare.py: per-stage error, heat map, PASS/FAIL
```

* **One interface per stage**: `(image, meta) -> (image, meta)` in Python; `stage(in, out, params)` in C.
  Adding a stage never touches the pipeline core.
* **Config, not code**: stage order and parameters live in `configs/*.yaml`.
* **Ground truth first**: `tools/make_synthetic.py` makes a Bayer RAW with known black level,
  illuminant gains, noise model and hot-pixel positions, so each module is checked against a known
  answer before it runs on real DNGs.
* **Firmware / hardware split**: statistics → gain estimation in float (firmware);
  gain application in fixed point (hardware), mirroring how a camera SoC divides the work.

## Repository layout

```
python_ref/mini_isp/   float reference: modules/, pipeline, synthetic data, RAW I/O
c_model/               fixed-point C11 model (include/isp.h, src/*.c, Makefile)
verify/                run C with Python's params, diff every stage
iq/                    image-quality metrics
tools/                 synthetic data, stage previews
docs/                  one engineering note per module
configs/               pipeline + verification tolerances
```

## References

* M. S. Brown, *Understanding Color and the In-Camera Image Processing Pipeline*, ICCV 2019 tutorial
* R. Sumner, *Processing RAW Images in MATLAB*
* H. S. Malvar, L. He, R. Cutler, *High-quality linear interpolation for demosaicing of Bayer-patterned color images*, ICASSP 2004
