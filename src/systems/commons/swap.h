#ifndef COMMON_SWAP_H
#define COMMON_SWAP_H

#include <stdbool.h>

struct swap_info
{
    long long used;
    long long total;
    float percent;
};


struct swap_info* init_swap(void);
bool get_swap_used(struct swap_info*);
bool get_swap_total(struct swap_info*);
bool get_swap_percent(struct swap_info*);

#endif
