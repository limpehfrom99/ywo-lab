/* Force-included (-include compat.h): Linux versions of the MSVC "_s" functions the book uses. */
#pragma once
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <stddef.h>
#ifdef __cplusplus
template <size_t N> inline int strcpy_s(char (&d)[N], const char *s) { snprintf(d, N, "%s", s); return 0; }
inline int strcpy_s(char *d, size_t n, const char *s) { snprintf(d, n, "%s", s); return 0; }
template <size_t N> inline int strcat_s(char (&d)[N], const char *s) { strncat(d, s, N - strlen(d) - 1); return 0; }
template <size_t N> inline int sprintf_s(char (&d)[N], const char *f, ...) { va_list a; va_start(a, f); int r = vsnprintf(d, N, f, a); va_end(a); return r; }
inline int fopen_s(FILE **fp, const char *name, const char *mode) {
   char m[8]; size_t j = 0;                       /* drop the Windows text-mode 't' flag */
   for (const char *c = mode; *c && j < sizeof(m) - 1; ++c) if (*c != 't') m[j++] = *c;
   m[j] = 0; *fp = fopen(name, m); return *fp ? 0 : 1; }
#endif
#define _int64 long long                 /* MSVC 64-bit integer keyword */
#define _heapchk() 0                     /* MSVC heap check: always "OK" here */
#define _HEAPOK 0
#define __min(a,b) (((a) < (b)) ? (a) : (b))   /* MSVC min/max macros */
#define __max(a,b) (((a) > (b)) ? (a) : (b))
