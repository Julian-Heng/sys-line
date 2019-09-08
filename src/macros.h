#ifndef MACROS_H
#define MACROS_H

#define _free(p) \
    if ((p)) \
    { \
        free((p)); \
        (p) = NULL; \
    }

#define _fclose(f) \
    if ((f)) \
    { \
        fclose((f)); \
        (f) = NULL; \
    }

#define _pclose(p) \
    if ((p)) \
    { \
        pclose((p)); \
        (p) = NULL; \
    }

#define percent(a, b) (((double)(a) / (double)(b)) * 100)

#endif
