#ifndef DARWIN_MEM_H
#define DARWIN_MEM_H
#if defined(__APPLE__) && defined(__MACH__)

#include "../commons/mem.h"

#define USED_REG " (wired|active|occupied)[^0-9]+([0-9]+)"

bool __get_mem_used(struct mem_info*);
bool __get_mem_total(struct mem_info*);

#endif
#endif
