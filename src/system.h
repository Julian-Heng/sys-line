#ifndef SYSTEM_H
#define SYSTEM_H

#ifndef STDIO_H
#include <stdio.h>
#endif

#ifndef CPU_H
#include "cpu.h"
#endif

struct system
{
    struct cpu_info* cpu;
};

struct system* init_system(void);

#endif
