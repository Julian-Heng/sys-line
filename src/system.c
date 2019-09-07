#include <stdio.h>
#include <stdlib.h>

#include "system.h"
#include "cpu.h"

struct system* init_system(void)
{
    struct system* sys;

    if ((sys = (struct system*)malloc(sizeof(struct system))))
    {
        sys->cpu = init_cpu();
    }

    return sys;
}
