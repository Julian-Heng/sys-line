#ifndef SYSTEM_H
#define SYSTEM_H

#ifndef STDIO_H
#include <stdio.h>
#endif

#ifndef CPU_H
#include "cpu.h"
#endif

#ifndef MEM_H
#include "mem.h"
#endif

struct system
{
    struct cpu_info* cpu;
    struct mem_info* mem;
};

struct system* init_system(void);

#endif
