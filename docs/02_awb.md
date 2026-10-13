# 02. Auto White Balance (Gray World)

<!-- 骨架已預填結構與實測數字；文字段落與分析請用你自己的話完成。
     下面兩個「待調查」問題是骨架跑出來的真實現象，非常適合當你第一篇筆記的核心。 -->

## 1. What it does
Estimate per-channel gains so a neutral surface gives R = G = B, then multiply each CFA site by its gain.
Gray world assumes the scene average is neutral: `gain_R = mean(G) / mean(R)`, `gain_B = mean(G) / mean(B)`.

## 2. Design decisions
- **Estimation in float, application in fixed point.** Mirrors firmware (3A runs on statistics) vs
  hardware (gain applied per pixel).
- **Exclude pixels ≥ 95 % of white level from statistics.**
  <!-- TODO: 為什麼？一個通道飽和時那個像素的顏色比例就失真了。 -->

## 3. Fixed-point implementation
`out = clip((in × gain_q + 2^9) >> 10, 0, white)`. Gains are Q3.10 (13 bits, max < 8.0).
`in × gain_q` ≤ 3839 × 8191 < 2^25, which fits in uint32.

| quantity | range | format | bits |
|---|---|---|---|
| input | 0–3839 | uint | 12 |
| gain | 0–7.999 | Q3.10 | 13 |
| product | < 2^25 | uint | 25 |
| output | 0–3839 | uint | 12 |

## 4. Results (synthetic scene, `make verify`)

| | gain R | gain B |
|---|---|---|
| ground truth | 1.8182 | 1.4286 |
| gray-world estimate | 1.8164 | 1.4616 |

| stage | max abs err | mean abs err | exact match |
|---|---|---|---|
| 02_awb | 1 DN | 0.070 | 92.98 % |

## 5. Analysis — 待調查
1. **B gain 偏了 2.3 %，R 幾乎正確。** 合成場景下半部有彩色色塊。為什麼 gray world 在這裡失準？
   改用 `gray_only=True` 的場景重跑看看（`tests/test_modules.py` 有範例）。
   再想想 white patch、gray edge 這類方法會不會比較好？
2. **C − Python 誤差分佈偏向 +1，而且越亮的區域越明顯**（見 `out/verify/02_awb_diff.png`）。
   gain 量化（1.81644 → 1860/1024 = 1.81641）理論上應該讓 C 偏小才對，為什麼反而偏大？
   提示：比較 Python `np.rint` 和 C `+ 2^9 >> 10` 的捨入規則，再算一下理論誤差上界。
   把 `ISP_GAIN_FRAC_BITS` 改成 8 或 12，誤差怎麼變？畫成圖。

## 6. Pitfalls I hit
<!-- TODO -->

## 7. References
- M. S. Brown, ICCV 2019 tutorial, white balance / color constancy section
