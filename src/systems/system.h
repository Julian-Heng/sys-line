#ifndef SYSTEM_H
#define SYSTEM_H

#include <stdio.h>

#include "commons/cpu.h"

struct system
{
    struct cpu_info* cpu;
};

struct system* init_system(void);

#endif
