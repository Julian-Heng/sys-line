#include <stdio.h>
#include <sys/utsname.h>

#include "systems/system.h"

int main(void)
{
    struct system_getter *sys = make_system();
    printf("%p\n", sys);
    printf("%p\n", sys->cpu_getter);
    return 0;
}
