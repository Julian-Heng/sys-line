#ifndef LINUX_SWAP_H
#define LINUX_SWAP_H
#if defined(__linux__)

#include "../commons/swap.h"

#define TOTAL_REG "^SwapTotal:\\s+([0-9]+)"
#define USED_REG "^SwapFree:\\s+([0-9]+)"

bool __get_swap_used(struct swap_info*);
bool __get_swap_total(struct swap_info*);

#endif
#endif
