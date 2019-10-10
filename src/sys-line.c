#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "systems/system.h"
#include "systems/commons/cpu.h"
#include "systems/commons/mem.h"
#include "systems/commons/swap.h"
#include "systems/commons/disk.h"

#include "sys-line.h"

int main(int argc, char** argv)
{
    struct system* sys;

    bool opts[5] = {
        [OPTION_ALL] = false,
        [DOMAIN_CPU] = false,
        [DOMAIN_MEM] = false,
        [DOMAIN_SWAP] = false,
        [DOMAIN_DISK] = false
    };

    parse_args(argc, argv, opts);

    if ((sys = init_system()))
    {
        printf("sys:\t%p\n", (void*)sys);
        if (opts[DOMAIN_CPU])  printf("cpu:\t%p\n", (void*)sys->cpu);
        if (opts[DOMAIN_MEM])  printf("mem:\t%p\n", (void*)sys->mem);
        if (opts[DOMAIN_SWAP]) printf("swap:\t%p\n", (void*)sys->swap);
        if (opts[DOMAIN_DISK]) printf("disk:\t%p\n", (void*)sys->disk);

        if (opts[DOMAIN_CPU])
        {
            get_cores(sys->cpu);
            get_cpu(sys->cpu);
            get_load(sys->cpu);
            get_cpu_usage(sys->cpu);
            get_fan(sys->cpu);
            get_temp(sys->cpu);
            get_uptime(sys->cpu);

            printf("cpu.cores:\t%d\n", sys->cpu->cores);
            printf("cpu.cpu:\t\"%s\"\n", sys->cpu->cpu);
            printf("cpu.load:\t%lf %lf %lf\n", sys->cpu->load[0],
                                               sys->cpu->load[1],
                                               sys->cpu->load[2]);
            printf("cpu.cpu_usage:\t%f\n", sys->cpu->cpu_usage);
            printf("cpu.fan:\t%d\n", sys->cpu->fan);
            printf("cpu.temp:\t%f\n", sys->cpu->temp);
            printf("cpu.uptime:\t%d\n", sys->cpu->uptime);
        }

        if (opts[DOMAIN_MEM])
        {
            get_mem_used(sys->mem);
            get_mem_total(sys->mem);
            get_mem_percent(sys->mem);

            printf("mem.used:\t%lld\n", sys->mem->used);
            printf("mem.total:\t%lld\n", sys->mem->total);
            printf("mem.percent:\t%f\n", sys->mem->percent);
        }

        if (opts[DOMAIN_SWAP])
        {
            get_swap_used(sys->swap);
            get_swap_total(sys->swap);
            get_swap_percent(sys->swap);

            printf("swap.used:\t%lld\n", sys->swap->used);
            printf("swap.total:\t%lld\n", sys->swap->total);
            printf("swap.percent:\t%f\n", sys->swap->percent);
        }

        if (opts[DOMAIN_DISK])
        {
            get_disk_dev(sys->disk);
            get_disk_name(sys->disk);
            get_disk_mount(sys->disk);
            get_disk_part(sys->disk);
            get_disk_used(sys->disk);
            get_disk_total(sys->disk);
            get_disk_percent(sys->disk);

            printf("disk.dev:\t\"%s\"\n", sys->disk->dev);
            printf("disk.name:\t\"%s\"\n", sys->disk->name);
            printf("disk.mount:\t\"%s\"\n", sys->disk->mount);
            printf("disk.part:\t\"%s\"\n", sys->disk->part);
            printf("disk.used:\t%lld\n", sys->disk->used);
            printf("disk.total:\t%lld\n", sys->disk->total);
            printf("disk.percent:\t%f\n", sys->disk->percent);
        }

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


void parse_args(int argc, char** argv, bool opts[5])
{
    do
    {
        if (! strcmp(*argv, "-a") || ! strcmp(*argv, "--all"))
            opts[OPTION_ALL] = true;
        else if (opts[OPTION_ALL] && ! strcmp(*argv, "cpu"))
            opts[DOMAIN_CPU] = true;
        else if (opts[OPTION_ALL] && ! strcmp(*argv, "mem"))
            opts[DOMAIN_MEM] = true;
        else if (opts[OPTION_ALL] && ! strcmp(*argv, "swap"))
            opts[DOMAIN_SWAP] = true;
        else if (opts[OPTION_ALL] && ! strcmp(*argv, "disk"))
            opts[DOMAIN_DISK] = true;
    } while (*++argv);
}
