#ifndef SYSTEM_H
#define SYSTEM_H

#include <stdio.h>

#include "commons/cpu.h"
#include "commons/mem.h"


struct system
{
    struct cpu_info* cpu;
    struct mem_info* mem;
};

struct system* init_system(void);

#endif
