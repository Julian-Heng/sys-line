#ifndef LINUX_MEM_H
#define LINUX_MEM_H
#if defined(__linux__)

#include "../commons/mem.h"

#define TOTAL_REG "^MemTotal:\\s+([0-9]+)"
#define USED_TOTAL_REG "^(MemTotal|Shmem):\\s+([0-9]+)"
#define USED_FREE_REG "^(MemFree|Buffers|Cached|SReclaimable):\\s+([0-9]+)"

bool __get_mem_used(struct mem_info*);
bool __get_mem_total(struct mem_info*);

#endif
#endif
