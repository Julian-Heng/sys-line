#ifndef SYSTEM_H
#define SYSTEM_H

#include <stdio.h>

struct cpu
{
    int cores;
    float speed;
    char cpu[BUFSIZ];
    char load_avg[BUFSIZ];
    float cpu_usage;
    int fan;
    float temp;
    char uptime[BUFSIZ];
} cpu;

struct system_getter
{
    struct cpu *cpu_getter;
} system_getter;

#endif
