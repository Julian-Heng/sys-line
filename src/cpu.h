#ifndef CPU_H
#define CPU_H

#ifndef STDIO_H
#include <stdio.h>
#endif

#ifndef STDBOOL_H
#include <stdbool.h>
#endif

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

bool get_uptime(struct cpu_info*);

#endif
