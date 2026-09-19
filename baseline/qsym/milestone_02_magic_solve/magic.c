#include <stdio.h>
#include <stdint.h>
#include <unistd.h>

int main(void) {
    uint8_t buf[4] = {0};
    ssize_t n = read(0, buf, 4);
    if (n < 4) return 1;

    if (buf[0] == 0xDE && buf[1] == 0xAD && buf[2] == 0xBE && buf[3] == 0xEF) {
        printf("MAGIC FOUND\n");
        if (buf[0] + buf[1] + buf[2] + buf[3] == 0x3E8) {
            printf("DEEP BRANCH\n");
        }
    }
    return 0;
}
