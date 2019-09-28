#ifndef SYSTEM_H
#define SYSTEM_H

#include <stdio.h>

#include "commons/cpu.h"
#include "commons/mem.h"
#include "commons/swap.h"
#include "commons/disk.h"


struct system
{
    struct cpu_info* cpu;
    struct mem_info* mem;
    struct swap_info* swap;
    struct disk_info* disk;
};

struct system* init_system(void);

#endif
