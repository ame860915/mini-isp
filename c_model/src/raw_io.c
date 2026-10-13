#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "isp.h"

int isp_img_alloc(isp_img_t *img, int w, int h, isp_cfa_t cfa, uint16_t white)
{
    img->width = w;
    img->height = h;
    img->cfa = cfa;
    img->white_level = white;
    img->data = (uint16_t *)calloc((size_t)w * h, sizeof(uint16_t));
    return img->data ? 0 : -1;
}

void isp_img_free(isp_img_t *img)
{
    free(img->data);
    img->data = NULL;
}

/* Little-endian uint16. Width/height must already be set (data allocated). */
int isp_read_raw(const char *path, isp_img_t *img)
{
    FILE *f = fopen(path, "rb");
    if (!f) { perror(path); return -1; }
    size_t n = (size_t)img->width * img->height;
    size_t got = fread(img->data, sizeof(uint16_t), n, f);
    fclose(f);
    if (got != n) {
        fprintf(stderr, "%s: expected %zu pixels, got %zu\n", path, n, got);
        return -1;
    }
    return 0;
}

int isp_write_raw(const char *path, const isp_img_t *img)
{
    FILE *f = fopen(path, "wb");
    if (!f) { perror(path); return -1; }
    size_t n = (size_t)img->width * img->height;
    size_t put = fwrite(img->data, sizeof(uint16_t), n, f);
    fclose(f);
    return put == n ? 0 : -1;
}

int isp_parse_cfa(const char *s, isp_cfa_t *cfa)
{
    static const char *names[] = {"RGGB", "BGGR", "GRBG", "GBRG"};
    for (int i = 0; i < 4; ++i)
        if (strcmp(s, names[i]) == 0) { *cfa = (isp_cfa_t)i; return 0; }
    return -1;
}

/* Channel of pixel (y, x) for each pattern: table[cfa][y&1][x&1]. */
isp_ch_t isp_cfa_channel(isp_cfa_t cfa, int y, int x)
{
    static const isp_ch_t t[4][2][2] = {
        {{CH_R, CH_GR}, {CH_GB, CH_B}},  /* RGGB */
        {{CH_B, CH_GB}, {CH_GR, CH_R}},  /* BGGR */
        {{CH_GR, CH_R}, {CH_B, CH_GB}},  /* GRBG */
        {{CH_GB, CH_B}, {CH_R, CH_GR}},  /* GBRG */
    };
    return t[cfa][y & 1][x & 1];
}

/* Firmware -> register conversion: round to nearest, saturate to 16 bits. */
uint16_t isp_float_to_gain_q(double g)
{
    double q = floor(g * ISP_GAIN_ONE + 0.5);
    if (q < 0) q = 0;
    if (q > 65535) q = 65535;
    return (uint16_t)q;
}
