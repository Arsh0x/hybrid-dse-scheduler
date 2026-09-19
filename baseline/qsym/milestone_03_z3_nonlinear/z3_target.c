#include <stdio.h>
#include <stdint.h>
#include <unistd.h>

int main(void) {
    uint8_t buf[4] = {0};
    ssize_t n = read(0, buf, 4);
    if (n < 4) return 1;

    /* Non-linear constraint: requires Z3 to solve */
    if (buf[0] * buf[1] == 0x1234) {
        printf("PRODUCT OK\n");
        /* Modular arithmetic: also forces Z3 */
        if ((buf[2] ^ 0xAA) == (buf[3] + 5)) {
            printf("XOR SUM OK\n");
        }
    }
    return 0;
}
