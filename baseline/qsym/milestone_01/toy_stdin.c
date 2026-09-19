#include <stdio.h>
#include <stdint.h>
#include <unistd.h>

int main(void) {
    uint8_t buf[4] = {0};
    ssize_t n = read(0, buf, 4);
    if (n <= 0) return 1;

    if (buf[0] > 10 && buf[1] < 20) {
        printf("Branch A\n");
        if (buf[2] == 0x42) {
            printf("Branch B\n");
        }
    }
    return 0;
}
