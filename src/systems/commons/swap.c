#if defined(__linux__)
#   include "../linux/swap.h"
#elif defined(__APPLE__) && defined(__MACH__)
#   include "../darwin/swap.h"
#endif

#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "../../utils/macros.h"
#include "swap.h"


struct swap_info* init_swap()
{
    struct swap_info* swap;

    if ((swap = (struct swap_info*)malloc(sizeof(struct swap_info))))
        memset(swap, 0, sizeof(struct swap_info));

    return swap;
}


bool get_swap_used(struct swap_info* swap)
{
    bool ret = false;

    if (! (ret = __get_swap_used(swap)))
        swap->used = 0;

    return ret;
}


bool get_swap_total(struct swap_info* swap)
{
    bool ret = false;

    if (! (ret = __get_swap_total(swap)))
        swap->total = 0;

    return ret;
}


bool get_swap_percent(struct swap_info* swap)
{
    if (! swap->used)
    {
        get_swap_used(swap);
        if (! swap->used)
            return false;
    }

    if (! swap->total)
    {
        get_swap_total(swap);
        if (! swap->total)
            return false;
    }

    swap->percent = percent(swap->used, swap->total);
    return true;
}
