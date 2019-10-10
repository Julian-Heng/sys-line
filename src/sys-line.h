#ifndef SYS_LINE_H
#define SYS_LINE_H

#include <stdbool.h>

enum OPTS
{
    OPTION_ALL,
    DOMAIN_CPU,
    DOMAIN_MEM,
    DOMAIN_SWAP,
    DOMAIN_DISK
};


void parse_args(int, char**, bool[5]);

#endif
