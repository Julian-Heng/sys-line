#include <stdio.h>
#include <stdlib.h>

#include "commons/cpu.h"
#include "commons/mem.h"
#include "commons/swap.h"
#include "commons/disk.h"

#include "system.h"

struct system* init_system(void)
{
    struct system* sys;

    if ((sys = (struct system*)malloc(sizeof(struct system))))
    {
        sys->cpu = init_cpu();
        sys->mem = init_mem();
        sys->swap = init_swap();
        sys->disk = init_disk();
    }

    return sys;
}


void clear_system(struct system* sys)
{
    clear_cpu(sys->cpu);
    clear_mem(sys->mem);
    clear_swap(sys->swap);
    clear_disk(sys->disk);
}
