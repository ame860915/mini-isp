# Data

Large files are not committed (see `.gitignore`).

| data | how to get it | used for |
|---|---|---|
| `synth.raw/.json` | `make synth` | unit-level ground truth (black level, gains, hot pixels) |
| Kodak 24 | download PNGs, re-mosaic with `mini_isp.synth.mosaic` | demosaic PSNR/SSIM benchmark |
| HDR+ burst dataset (Pixel DNG) | download a small subset | real RAW + Google's output for side-by-side comparison |
| your own phone DNGs (Open Camera) | flat field, ColorChecker, gray card at several ISOs | LSC / CCM / noise calibration |
