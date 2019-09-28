#include <stdio.h>
#include <stdlib.h>

#include "systems/system.h"
#include "systems/commons/cpu.h"
#include "systems/commons/mem.h"
#include "systems/commons/swap.h"
#include "systems/commons/disk.h"


int main()
{
    struct system* sys;

    if ((sys = init_system()))
    {
        printf("sys:\t%p\n", (void*)sys);
        printf("cpu:\t%p\n", (void*)sys->cpu);
        printf("mem:\t%p\n", (void*)sys->mem);
        printf("swap:\t%p\n", (void*)sys->swap);
        printf("disk:\t%p\n", (void*)sys->disk);

        get_cores(sys->cpu);
        printf("cpu.cores:\t%d\n", sys->cpu->cores);

        get_cpu(sys->cpu);
        printf("cpu.cpu:\t\"%s\"\n", sys->cpu->cpu);

        get_load(sys->cpu);
        printf("cpu.load:\t%f %f %f\n", sys->cpu->load[0],
                                        sys->cpu->load[1],
                                        sys->cpu->load[2]);

        get_cpu_usage(sys->cpu);
        printf("cpu.cpu_usage:\t%f\n", sys->cpu->cpu_usage);

        get_fan(sys->cpu);
        printf("cpu.fan:\t%d\n", sys->cpu->fan);

        get_temp(sys->cpu);
        printf("cpu.temp:\t%f\n", sys->cpu->temp);

        get_uptime(sys->cpu);
        printf("cpu.uptime:\t%d\n", sys->cpu->uptime);

        get_mem_used(sys->mem);
        printf("mem.used:\t%lld\n", sys->mem->used);

        get_mem_total(sys->mem);
        printf("mem.total:\t%lld\n", sys->mem->total);

        get_mem_percent(sys->mem);
        printf("mem.percent:\t%f\n", sys->mem->percent);

        get_swap_used(sys->swap);
        printf("swap.used:\t%lld\n", sys->swap->used);

        get_swap_total(sys->swap);
        printf("swap.total:\t%lld\n", sys->swap->total);

        get_swap_percent(sys->swap);
        printf("swap.percent:\t%f\n", sys->swap->percent);

        get_disk_dev(sys->disk);
        printf("disk.dev:\t\"%s\"\n", sys->disk->dev);

        get_disk_name(sys->disk);
        printf("disk.name:\t\"%s\"\n", sys->disk->name);

        get_disk_mount(sys->disk);
        printf("disk.mount:\t\"%s\"\n", sys->disk->mount);

        get_disk_part(sys->disk);
        printf("disk.part:\t\"%s\"\n", sys->disk->part);

        get_disk_used(sys->disk);
        printf("disk.used:\t%lld\n", sys->disk->used);

        get_disk_total(sys->disk);
        printf("disk.total:\t%lld\n", sys->disk->total);

        get_disk_percent(sys->disk);
        printf("disk.percent:\t%f\n", sys->disk->percent);

        free(sys->cpu);
        sys->cpu = NULL;

        free(sys->mem);
        sys->mem = NULL;

        free(sys->swap);
        sys->swap = NULL;

        free(sys->disk);
        sys->disk = NULL;

        free(sys);
        sys = NULL;
    }

    return 0;
}
