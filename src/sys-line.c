#include <stdio.h>
#include <stdlib.h>

#include "system.h"
#include "cpu.h"

int main(void)
{
    struct system* sys;

    sys = init_system();

    if (sys)
    {
        get_cores(sys->cpu);
        get_cpu(sys->cpu);
        get_load(sys->cpu);
        get_cpu_usage(sys->cpu);

        get_uptime(sys->cpu);

        printf("sys:\t%p\n", (void*)sys);
        printf("cpu:\t%p\n", (void*)sys->cpu);
        printf("cpu.cores:\t%d\n", sys->cpu->cores);
        printf("cpu.cpu:\t%s\n", sys->cpu->cpu);
        printf("cpu.load:\t%f %f %f\n", sys->cpu->load[0],
                                        sys->cpu->load[1],
                                        sys->cpu->load[2]);
        printf("cpu.cpu_usage:\t%f\n", sys->cpu->cpu_usage);
        printf("cpu.fan:\t%d\n", sys->cpu->fan);
        printf("cpu.temp:\t%f\n", sys->cpu->temp);
        printf("cpu.uptime:\t%d\n", sys->cpu->uptime);

        free(sys->cpu);
        sys->cpu = NULL;

        free(sys);
        sys = NULL;
    }

    return 0;
}
