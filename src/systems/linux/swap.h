#ifndef LINUX_SWAP_H
#define LINUX_SWAP_H
#if defined(__linux__)

#include "../commons/swap.h"

bool __get_swap_used(struct swap_info*);
bool __get_swap_total(struct swap_info*);

#endif
#endif
