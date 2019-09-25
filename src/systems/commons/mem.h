#ifndef COMMON_MEM_H
#define COMMON_MEM_H

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

struct mem_info
{
    long long used;
    long long total;
    float percent;
};


struct mem_info* init_mem(void);
bool get_mem_used(struct mem_info*);
bool get_mem_total(struct mem_info*);
bool get_mem_percent(struct mem_info*);

#endif
