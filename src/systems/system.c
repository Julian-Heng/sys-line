#include <stdio.h>
#include <stdlib.h>

#include "commons/cpu.h"
#include "commons/mem.h"

#include "system.h"

struct system* init_system(void)
{
    struct system* sys;

    if ((sys = (struct system*)malloc(sizeof(struct system))))
    {
        sys->cpu = init_cpu();
        sys->mem = init_mem();
    }

    return sys;
}
