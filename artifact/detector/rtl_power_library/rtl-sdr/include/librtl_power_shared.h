#ifndef LIB_RTL_POWER_SHARED_H
#define LIB_RTL_POWER_SHARED_H
// int rtl_power_python(CALLBACK cb, const char* a_freq_optarg, int a_gain, int a_interval,int a_exit_time);
typedef int (*CALLBACK)(double *,double *,int,int);
int read_rtl_sdr_samples(CALLBACK cb);
int close_rtlsdr(int a);
int init_rtl_sdr( const char* a_freq_optarg, int a_gain, double a_interval,double a_exit_time);
int change_setting( const char* a_freq_optarg);
#endif