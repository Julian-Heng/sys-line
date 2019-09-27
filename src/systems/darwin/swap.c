#if defined(__APPLE__) && defined(__MACH__)

#include <sys/sysctl.h>
#include <sys/types.h>

#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#include "../commons/swap.h"

#include "swap.h"


static bool is_sysctl_set = false;
static void set_sysctl_out(void);

static struct xsw_usage sysctl_out;

bool __get_swap_used(struct swap_info* swap)
{
    if (! is_sysctl_set)
    {
        set_sysctl_out();
        if (! is_sysctl_set)
            return false;
    }

    swap->used = sysctl_out.xsu_used;
    return true;
}


bool __get_swap_total(struct swap_info* swap)
{
    if (! is_sysctl_set)
    {
        set_sysctl_out();
        if (! is_sysctl_set)
            return false;
    }

    swap->total = sysctl_out.xsu_total;
    return true;
}


static void set_sysctl_out()
{
    size_t len = sizeof(sysctl_out);
    sysctlbyname("vm.swapusage", &sysctl_out, &len, NULL, 0);
    is_sysctl_set = true;
}

#endif
