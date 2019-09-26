#ifndef DARWIN_CPU_H
#define DARWIN_CPU_H
#if defined(__APPLE__) && defined(__MACH__)

#include "../commons/cpu.h"

bool __get_cores(struct cpu_info*);
bool __get_cpu(struct cpu_info*, float*);
bool __get_load(struct cpu_info*);
bool __get_fan(struct cpu_info*);
bool __get_temp(struct cpu_info*);
bool __get_uptime(struct cpu_info*);

#endif
#endif
