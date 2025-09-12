
#ifndef RTL_POWER_SHARED_EXPORT_H
#define RTL_POWER_SHARED_EXPORT_H

#ifdef RTL_POWER_SHARED_STATIC_DEFINE
#  define RTL_POWER_SHARED_EXPORT
#  define RTL_POWER_SHARED_NO_EXPORT
#else
#  ifndef RTL_POWER_SHARED_EXPORT
#    ifdef rtl_power_EXPORTS
        /* We are building this library */
#      define RTL_POWER_SHARED_EXPORT __attribute__((visibility("default")))
#    else
        /* We are using this library */
#      define RTL_POWER_SHARED_EXPORT __attribute__((visibility("default")))
#    endif
#  endif

#  ifndef RTL_POWER_SHARED_NO_EXPORT
#    define RTL_POWER_SHARED_NO_EXPORT __attribute__((visibility("hidden")))
#  endif
#endif

#ifndef RTL_POWER_SHARED_DEPRECATED
#  define RTL_POWER_SHARED_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef RTL_POWER_SHARED_DEPRECATED_EXPORT
#  define RTL_POWER_SHARED_DEPRECATED_EXPORT RTL_POWER_SHARED_EXPORT RTL_POWER_SHARED_DEPRECATED
#endif

#ifndef RTL_POWER_SHARED_DEPRECATED_NO_EXPORT
#  define RTL_POWER_SHARED_DEPRECATED_NO_EXPORT RTL_POWER_SHARED_NO_EXPORT RTL_POWER_SHARED_DEPRECATED
#endif

#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef RTL_POWER_SHARED_NO_DEPRECATED
#    define RTL_POWER_SHARED_NO_DEPRECATED
#  endif
#endif

#endif /* RTL_POWER_SHARED_EXPORT_H */
