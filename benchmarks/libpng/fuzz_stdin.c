#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include "png.h"

#define MAX_SIZE (256 * 1024)
static uint8_t buf[MAX_SIZE];

static void read_stdin_to_buf(size_t *out_len) {
    size_t total = 0;
    ssize_t n;
    while ((n = read(0, buf + total, MAX_SIZE - total)) > 0) {
        total += n;
        if (total >= MAX_SIZE) break;
    }
    *out_len = total;
}

int main(void) {
    size_t len = 0;
    read_stdin_to_buf(&len);
    if (len < 8) return 1;

    png_structp png = png_create_read_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    if (!png) return 1;
    png_infop info = png_create_info_struct(png);
    if (!info) {
        png_destroy_read_struct(&png, NULL, NULL);
        return 1;
    }
    if (setjmp(png_jmpbuf(png))) {
        png_destroy_read_struct(&png, &info, NULL);
        return 1;
    }

    FILE *f = fmemopen((void*)buf, len, "rb");
    if (!f) {
        png_destroy_read_struct(&png, &info, NULL);
        return 1;
    }
    png_init_io(png, f);
    png_read_info(png, info);

    png_uint_32 w = png_get_image_width(png, info);
    png_uint_32 h = png_get_image_height(png, info);
    int bit_depth = png_get_bit_depth(png, info);
    int color_type = png_get_color_type(png, info);

    if (w > 2048 || h > 2048) {
        fclose(f);
        png_destroy_read_struct(&png, &info, NULL);
        return 1;
    }

    if (bit_depth == 16) png_set_strip_16(png);
    if (color_type == PNG_COLOR_TYPE_PALETTE) png_set_palette_to_rgb(png);
    if (color_type == PNG_COLOR_TYPE_GRAY && bit_depth < 8) png_set_expand_gray_1_2_4_to_8(png);
    if (png_get_valid(png, info, PNG_INFO_tRNS)) png_set_tRNS_to_alpha(png);
    png_set_filler(png, 0xff, PNG_FILLER_AFTER);
    png_read_update_info(png, info);

    size_t rowbytes = png_get_rowbytes(png, info);
    png_bytep *rows = malloc(h * sizeof(png_bytep));
    if (!rows) { fclose(f); png_destroy_read_struct(&png, &info, NULL); return 1; }
    for (png_uint_32 y = 0; y < h; y++) {
        rows[y] = malloc(rowbytes);
        if (!rows[y]) break;
    }
    png_read_image(png, rows);

    for (png_uint_32 y = 0; y < h; y++) free(rows[y]);
    free(rows);
    fclose(f);
    png_destroy_read_struct(&png, &info, NULL);
    return 0;
}
