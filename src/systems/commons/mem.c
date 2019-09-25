#if defined(__linux__)
#   include "../linux/mem.h"
#endif

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../../utils/macros.h"
#include "../../utils/tools.h"

#include "mem.h"


struct mem_info* init_mem()
{
    struct mem_info* mem;

    if ((mem = (struct mem_info*)malloc(sizeof(struct mem_info))))
        memset(mem, 0, sizeof(struct mem_info));

    return mem;
}


bool get_mem_used(struct mem_info* mem)
{
    bool ret = false;

    if (! (ret = __get_mem_used(mem)))
        mem->used = 0;

    return ret;
}


bool get_mem_total(struct mem_info* mem)
{
    bool ret = false;

    if (! (ret = __get_mem_total(mem)))
        mem->total = 0;

    return ret;
}


bool get_mem_percent(struct mem_info* mem)
{
    if (! mem->used)
        get_mem_used(mem);
    if (! mem->used)
        return false;

    if (! mem->total)
        get_mem_total(mem);
    if (! mem->total)
        return false;

    mem->percent = percent(mem->used, mem->total);
    return true;
}
