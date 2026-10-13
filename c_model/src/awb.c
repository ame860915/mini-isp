#include "isp.h"

/*
 * Per-CFA-site gain, fixed point:
 *   out = clip((in * gain_q + 0.5 LSB) >> FRAC, 0, white_level)
 * in (<=16 bit) * gain_q (<=16 bit) fits in uint32_t.
 *
 * Error sources vs the float reference (document these in docs/02_awb.md):
 *   1. gain quantisation  |g - gain_q/2^F| <= 2^-(F+1)
 *   2. output rounding    <= 0.5 DN
 */
int isp_awb_apply(const isp_img_t *in, isp_img_t *out, const awb_params_t *p)
{
    const uint32_t round = 1u << (ISP_GAIN_FRAC_BITS - 1);
    const uint32_t wl = in->white_level;
    for (int y = 0; y < in->height; ++y) {
        const uint16_t *src = in->data + (size_t)y * in->width;
        uint16_t *dst = out->data + (size_t)y * in->width;
        for (int x = 0; x < in->width; ++x) {
            uint32_t g = p->gain_q[isp_cfa_channel(in->cfa, y, x)];
            uint32_t v = ((uint32_t)src[x] * g + round) >> ISP_GAIN_FRAC_BITS;
            dst[x] = (uint16_t)(v > wl ? wl : v);
        }
    }
    out->white_level = in->white_level;
    return 0;
}
