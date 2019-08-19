#include <stdio.h>
#include <sys/utsname.h>

#ifdef __linux__
#include "systems/linux.h"
#endif

int main(void)
{
    printf("sys-line\n");
    return 0;
}
