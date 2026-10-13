/*
 * mini_isp_c: run the fixed-point pipeline and dump every stage.
 *
 *   mini_isp_c --input in.raw --width W --height H --cfa RGGB \
 *              --black 256 --white 4095 --gain_r 1.9 --gain_b 1.6 --out out/c
 *
 * Stage dumps use the same names as the Python reference (01_blc.raw, 02_awb.raw)
 * so verify/compare.py can diff them directly.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "isp.h"

typedef struct {
    const char *input, *out, *cfa;
    int width, height, black, white;
    double gain_r, gain_g, gain_b;
} args_t;

static void usage(void)
{
    fprintf(stderr,
            "usage: mini_isp_c --input F --width W --height H --cfa RGGB --black N --white N\n"
            "                  [--gain_r G] [--gain_g G] [--gain_b G] [--out DIR]\n");
}

static int parse(int argc, char **argv, args_t *a)
{
    *a = (args_t){.out = "out/c", .cfa = "RGGB", .gain_r = 1.0, .gain_g = 1.0, .gain_b = 1.0};
    for (int i = 1; i < argc; ++i) {
        const char *k = argv[i];
        if (i + 1 >= argc) { usage(); return -1; }
        const char *v = argv[++i];
        if      (!strcmp(k, "--input"))  a->input = v;
        else if (!strcmp(k, "--out"))    a->out = v;
        else if (!strcmp(k, "--cfa"))    a->cfa = v;
        else if (!strcmp(k, "--width"))  a->width = atoi(v);
        else if (!strcmp(k, "--height")) a->height = atoi(v);
        else if (!strcmp(k, "--black"))  a->black = atoi(v);
        else if (!strcmp(k, "--white"))  a->white = atoi(v);
        else if (!strcmp(k, "--gain_r")) a->gain_r = atof(v);
        else if (!strcmp(k, "--gain_g")) a->gain_g = atof(v);
        else if (!strcmp(k, "--gain_b")) a->gain_b = atof(v);
        else { fprintf(stderr, "unknown arg %s\n", k); usage(); return -1; }
    }
    if (!a->input || a->width <= 0 || a->height <= 0 || a->white <= 0) { usage(); return -1; }
    return 0;
}

static int dump(const char *dir, const char *name, const isp_img_t *img)
{
    char path[1024];
    snprintf(path, sizeof path, "%s/%s.raw", dir, name);
    return isp_write_raw(path, img);
}

int main(int argc, char **argv)
{
    args_t a;
    if (parse(argc, argv, &a)) return 2;

    isp_cfa_t cfa;
    if (isp_parse_cfa(a.cfa, &cfa)) { fprintf(stderr, "bad cfa %s\n", a.cfa); return 2; }

    isp_img_t buf0, buf1;
    if (isp_img_alloc(&buf0, a.width, a.height, cfa, (uint16_t)a.white) ||
        isp_img_alloc(&buf1, a.width, a.height, cfa, (uint16_t)a.white)) {
        fprintf(stderr, "out of memory\n");
        return 1;
    }
    if (isp_read_raw(a.input, &buf0)) return 1;

    /* 01 BLC */
    blc_params_t blc = {.black_level = (uint16_t)a.black};
    isp_blc(&buf0, &buf1, &blc);
    if (dump(a.out, "01_blc", &buf1)) return 1;

    /* 02 AWB (gains come from firmware / Python estimate) */
    uint16_t gr = isp_float_to_gain_q(a.gain_r), gg = isp_float_to_gain_q(a.gain_g),
             gb = isp_float_to_gain_q(a.gain_b);
    awb_params_t awb = {.gain_q = {[CH_R] = gr, [CH_GR] = gg, [CH_GB] = gg, [CH_B] = gb}};
    buf0.white_level = buf1.white_level;
    isp_awb_apply(&buf1, &buf0, &awb);
    if (dump(a.out, "02_awb", &buf0)) return 1;

    printf("[c ] gains Q%d: R=%u G=%u B=%u  -> %s\n", ISP_GAIN_FRAC_BITS, gr, gg, gb, a.out);

    /* TODO(M2+): dpc -> demosaic -> ccm -> gamma, ping-ponging buf0/buf1 */

    isp_img_free(&buf0);
    isp_img_free(&buf1);
    return 0;
}
