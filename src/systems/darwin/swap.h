#ifndef DARWIN_SWAP_H
#define DARWIN_SWAP_H
#if defined(__APPLE__) && defined(__MACH__)

#include "../commons/swap.h"

bool __get_swap_used(struct swap_info*);
bool __get_swap_total(struct swap_info*);

#endif
#endif
