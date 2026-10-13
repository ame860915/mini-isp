# Roadmap

Each milestone = Python ref + tests + C fixed-point + verify tolerance + docs note + git tag.

- [x] **M0 skeleton** — interface, synthetic RAW, C model build, stage-by-stage verify, CI
- [x] **M1 BLC + AWB (gray world)** — bit-exact BLC, Q3.10 gains ≤ 1 DN *(finish docs/02 analysis)*
- [ ] **M2 DPC** — detect against 8 same-colour neighbours; recall/precision vs `gt.hot_pixels`
- [ ] **M3 Demosaic** — bilinear, then Malvar-He-Cutler; PSNR/SSIM on Kodak 24; zipper / false colour analysis; fixed-point kernels without division
- [ ] **M4 Real DNG** — rawpy input, run on HDR+ subset, side-by-side with reference JPEG
- [ ] **M5 CCM + Gamma** — 3×3 matrix in Q format, gamma as LUT (LUT size vs error trade-off), sRGB output
- [ ] **M6 IQ metrics** — SSIM, ΔE2000 (ColorChecker), slanted-edge MTF50; repeatability over 10 captures
- [ ] **M7 Calibration** — LSC gain grid from flat field, CCM least-squares from ColorChecker, noise profile vs ISO
- [ ] **M8 Tuning tool** — parameter sweep / search over NR & sharpening against IQ metrics, results logged
