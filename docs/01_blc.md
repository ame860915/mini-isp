# 01. Black Level Correction

<!-- 骨架已預填結構與實測數字；文字段落請用你自己的話完成。 -->

## 1. What it does
`out = max(raw − black_level, 0)`; usable range becomes `[0, white_level − black_level]`.
<!-- TODO: 為什麼 sensor 全黑時讀值不是 0？（dark current、ADC offset、pedestal 的目的） -->

## 2. Design decisions
- Clip at 0 instead of keeping negative values.
  <!-- TODO: 這會讓暗部雜訊的平均值偏高（雜訊被截斷成單邊分佈）。之後做降噪時要不要保留負值？查 HDR+ / Unprocessing 論文怎麼處理。 -->
- Single global black level for all four CFA sites.
  <!-- TODO: 真實 DNG 的 black_level_per_channel 四個值一樣嗎？用一張 Pixel DNG 驗證。 -->

## 3. Fixed-point implementation
Pure integer subtraction with saturation; bit-exact against the reference.

| quantity | range | format | bits |
|---|---|---|---|
| input | 0–4095 | uint | 12 |
| output | 0–3839 | uint | 12 |

## 4. Results
| stage | max abs err | exact match |
|---|---|---|
| 01_blc | 0 DN | 100 % |

## 5. Analysis
<!-- TODO -->

## 6. Pitfalls I hit
<!-- TODO -->

## 7. References
- R. Sumner, *Processing RAW Images in MATLAB*, §Linearization
