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

#define file_exist(f) access((f), F_OK) != -1
#define percent(a, b) ((b) ? (((double)(a) / (double)(b)) * 100) : 0)

#endif
