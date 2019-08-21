#include "system.h"

#if defined(__APPLE__) && defined(__MACH__)
#include "darwin.h"
#endif

struct system_getter *make_system()
{
    return _make_system();
}
