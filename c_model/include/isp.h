/*
 * mini-isp fixed-point C model.
 *
 * Conventions
 *   - Pixel data: uint16_t, single Bayer plane, row-major.
 *   - All arithmetic is integer. Gains are unsigned fixed point with
 *     ISP_GAIN_FRAC_BITS fractional bits (Q3.10 fits gains < 8.0 in 13 bits).
 *   - Every stage has the signature  int stage(const isp_img_t *in, isp_img_t *out, const params*)
 *     so stages can be chained and dumped for verification.
 */
#ifndef MINI_ISP_H
#define MINI_ISP_H

#include <stddef.h>
#include <stdint.h>

#define ISP_GAIN_FRAC_BITS 10
#define ISP_GAIN_ONE (1u << ISP_GAIN_FRAC_BITS)

typedef enum { CFA_RGGB = 0, CFA_BGGR, CFA_GRBG, CFA_GBRG } isp_cfa_t;
typedef enum { CH_R = 0, CH_GR, CH_GB, CH_B } isp_ch_t;

typedef struct {
    int width, height;
    isp_cfa_t cfa;
    uint16_t white_level; /* max valid code value in this domain */
    uint16_t *data;
} isp_img_t;

typedef struct {
    uint16_t black_level;
} blc_params_t;

typedef struct {
    uint16_t gain_q[4]; /* indexed by isp_ch_t, fixed point Q.ISP_GAIN_FRAC_BITS */
} awb_params_t;

/* image helpers (raw_io.c) */
int  isp_img_alloc(isp_img_t *img, int w, int h, isp_cfa_t cfa, uint16_t white);
void isp_img_free(isp_img_t *img);
int  isp_read_raw(const char *path, isp_img_t *img);
int  isp_write_raw(const char *path, const isp_img_t *img);
int  isp_parse_cfa(const char *s, isp_cfa_t *cfa);
isp_ch_t isp_cfa_channel(isp_cfa_t cfa, int y, int x);
uint16_t isp_float_to_gain_q(double g);

/* stages */
int isp_blc(const isp_img_t *in, isp_img_t *out, const blc_params_t *p);
int isp_awb_apply(const isp_img_t *in, isp_img_t *out, const awb_params_t *p);

#endif
