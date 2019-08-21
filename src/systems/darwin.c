#include <stdlib.h>

#include "darwin.h"
#include "system.h"

struct system_getter *_make_system()
{
    struct system_getter *sys = NULL;

    if ((sys = (struct system_getter*)malloc(sizeof(struct system_getter))))
    {
        if (! (sys->cpu_getter = (struct cpu*)malloc(sizeof(struct cpu))))
        {
        }
    }

    return sys;
}
