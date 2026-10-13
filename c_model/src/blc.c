#include "isp.h"

/* out = max(in - black_level, 0). Integer-exact vs the float reference. */
int isp_blc(const isp_img_t *in, isp_img_t *out, const blc_params_t *p)
{
    const int n = in->width * in->height;
    const uint16_t bl = p->black_level;
    for (int i = 0; i < n; ++i) {
        uint16_t v = in->data[i];
        out->data[i] = v > bl ? (uint16_t)(v - bl) : 0;
    }
    out->white_level = in->white_level > bl ? (uint16_t)(in->white_level - bl) : 0;
    return 0;
}
