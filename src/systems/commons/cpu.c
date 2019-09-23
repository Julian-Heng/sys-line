#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#include "../../utils/tools.h"

#include "cpu.h"

#if defined(__linux__)
#   include "../linux/cpu.h"
#endif


struct cpu_info* init_cpu(void)
{
    struct cpu_info* cpu;

    if ((cpu = (struct cpu_info*)malloc(sizeof(struct cpu_info))))
        memset(cpu, 0, sizeof(struct cpu_info));

    return cpu;
}


bool get_cores(struct cpu_info* cpu)
{
    bool ret = false;

    if (! (ret = __get_cores(cpu)))
        cpu->cores = 0;

    return ret;
}


bool get_cpu(struct cpu_info* cpu)
{
    bool ret = false;

    float speed = 0.0f;
    char cpu_replace[BUFSIZ];
    char cpu_regex[BUFSIZ];

    ret = __get_cpu(cpu, &speed);

    if (ret)
    {
        if (speed > 0.0f)
        {
            snprintf(cpu_replace, BUFSIZ, "(%d) @ %0.1fGHz", cpu->cores, speed);
            snprintf(cpu_regex, BUFSIZ, "@ ([0-9]+\\.)?[0-9]+GHz");
        }
        else
        {
            snprintf(cpu_replace, BUFSIZ, "(%d) @", cpu->cores);
            snprintf(cpu_regex, BUFSIZ, "@");
        }

        re_replace(cpu_regex, cpu_replace, cpu->cpu, BUFSIZ);
        re_replace_all("CPU|\\((R|TM)\\)", "", cpu->cpu, BUFSIZ);
        trim(cpu->cpu);
    }
    else
        memset(cpu->cpu, 0, BUFSIZ);

    return ret;
}


bool get_load(struct cpu_info* cpu)
{
    bool ret = false;

    if (! (ret = __get_load(cpu)))
        memset(cpu->load, 0, 3 * sizeof(float));

    return ret;
}


bool get_cpu_usage(struct cpu_info* cpu)
{
    bool ret = false;

    FILE* ps;
    char buf[BUFSIZ];
    float val = 0.0f;

    if (! cpu->cores)
        get_cores(cpu);
    if (! cpu->cores)
        return ret;

    if ((ret = (ps = popen("ps -e -o %cpu", "r"))))
    {
        memset(buf, 0, BUFSIZ);

        while (fgets(buf, BUFSIZ, ps))
            if (sscanf(buf, "%f", &val) == 1)
                cpu->cpu_usage += val;

        cpu->cpu_usage /= cpu->cores;
        pclose(ps);
    }

    return ret;
}


bool get_fan(struct cpu_info* cpu)
{
    bool ret = false;

    if (! (ret = __get_fan(cpu)))
        cpu->fan = 0.0f;

    return ret;
}


bool get_temp(struct cpu_info* cpu)
{
    bool ret = false;

    if (! (ret = __get_temp(cpu)))
        cpu->temp = 0.0f;

    return ret;
}


bool get_uptime(struct cpu_info* cpu)
{
    bool ret = false;

    if (! (ret = __get_uptime(cpu)))
        cpu->uptime = 0.0f;

    return ret;
}
