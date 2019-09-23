#ifndef COMMON_CPU_H
#define COMMON_CPU_H

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

struct cpu_info
{
    int cores;
    char cpu[BUFSIZ];
    float load[3];
    float cpu_usage;
    int fan;
    float temp;
    int uptime;
};


struct cpu_info* init_cpu(void);
bool get_cores(struct cpu_info*);
bool get_cpu(struct cpu_info*);
bool get_load(struct cpu_info*);
bool get_cpu_usage(struct cpu_info*);
bool get_fan(struct cpu_info*);
bool get_temp(struct cpu_info*);
bool get_uptime(struct cpu_info*);

#endif
