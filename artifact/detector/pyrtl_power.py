import ctypes
from ctypes import *
import subprocess
import time
import numpy as np


init_rtl_sdr = None
read_rtl_sdr_samples = None
close_rtlsdr = None
change_setting = None
rtl_device = False
enable_file_save = None
buffer = []

class FrequencyScanSetting:
    """
    Python wrapper to handle RTL-SDR scanning
    """
    start_frequency = ""
    end_frequency = ""
    bin_size = ""

    def __init__(self):
        self.start_frequency: str = ""
        self.end_frequency: str = ""
        self.bin_size: str = ""

    def __init__(self,start:str,end:str,binsize:str):
        self.start_frequency:str = start
        self.end_frequency:str = end
        self.bin_size:str = binsize

    def validate_all_setting(self):
        for i in [self.start_frequency,self.end_frequency,self.bin_size]:
            if len(i) == 0:
                return False
        if self.validate_binsize() is False:
            return False
        if self.validate_range() is False:
            return False
        return True

    def validate_range(self):
        f1 = self.str_to_int(self.start_frequency)
        f2 = self.str_to_int(self.start_frequency)
        if f1 > f2:
            return False
        return True

    def validate_binsize(self):
        b1 = self.str_to_int(self.bin_size)
        if 1 < b1 and b1 <= 2.8*10**6:
            return True
        return False
    def str_to_int(self,s_:str):
        if "k" in s_:
            num = int(s_[0:s_.find("k")])
            num = num * 10 ** 3
            return num
        if "M" in s_:
            num = int(s_[0:s_.find("M")])
            num = num * 10 ** 6
            return num
        if "G" in s_:
            num = int(s_[0:s_.find("G")])
            num = num * 10 ** 9
            return num
        return int(s_)
    def __str__(self):
        return "%s:%s:%s" % (self.start_frequency,self.end_frequency,self.bin_size)

setting = FrequencyScanSetting("100M","480M","8k")
@CFUNCTYPE(c_int,POINTER(c_double),POINTER(c_double), c_int, c_int)
def py_callback(data_header, data,len_header,len_data):
    """
    Callback function for RTL-POWER library. For every scan, this will be called
    :param data_header: Header information for RTL-POWER scan, mostly frequency bins labels
    :param data: Signal data for RTL-POWER scan
    :param len_header: length of header
    :param len_data: length of data
    """
    h_data = np.fromiter(data_header,dtype=np.double,count=len_header)
    rtl_data = np.fromiter(data, dtype=np.double, count=len_data)
    buffer.append([h_data,rtl_data])
    print(len_header,len_data)
    return 0

def load_lib():
    """
    Load C level RTL-POWER library and map functions to python end points manually due to python C library bugs.
    """
    global init_rtl_sdr,read_rtl_sdr_samples,close_rtlsdr,change_setting
    # Shared Library location and name
    lib_path = './rtl_power_library/rtl-sdr/build/src/librtl_power_shared.so.0.6git'

    # grab raw symbol map for native architecture
    raw_symbols = subprocess.check_output(['/usr/bin/nm', lib_path]).decode('utf-8').rstrip().split('\n')
    # filter nm output for one known resolvable symbol and the desired to calculate offsets
    known_public_symbol = 'rtlsdr_set_center_freq'

    # desired function symbol
    desired_symbol1 = 'init_rtl_sdr'
    desired_symbol2 = 'read_rtl_sdr_samples'
    desired_symbol3 = 'close_rtlsdr'
    desired_symbol4 = 'change_setting'
    desired_symbol5 = 'enable_file_save'

    filter_names = [known_public_symbol, desired_symbol1,desired_symbol2,desired_symbol3,desired_symbol4,desired_symbol5]
    filtered_symbols = [x.split(' ', 3) for x in raw_symbols if x.split(' ', 3)[-1] in filter_names]
    syms = dict()
    for x in filtered_symbols:
        syms[x[-1]] = int('0x'+x[0], 0)

    # calculate the offset (function address offsets)
    offset1 = syms[desired_symbol1] - syms[known_public_symbol]
    offset2 = syms[desired_symbol2] - syms[known_public_symbol]
    offset3 = syms[desired_symbol3] - syms[known_public_symbol]
    offset4 = syms[desired_symbol4] - syms[known_public_symbol]

    # load the library
    lib_obj = cdll.LoadLibrary(lib_path)
    public_addr = ctypes.cast(lib_obj[known_public_symbol], ctypes.c_void_p).value

    # calculate C function's address in memory
    private_addr1 = public_addr + offset1
    private_addr2 = public_addr + offset2
    private_addr3 = public_addr + offset3
    private_addr4 = public_addr + offset4


    #mapping python fuction variables and C fuction memory addresses
    init_rtl_sdr = ctypes.CFUNCTYPE(c_int)(private_addr1)
    init_rtl_sdr.argtypes=[c_char_p,c_int,c_double,c_double]
    read_rtl_sdr_samples = ctypes.CFUNCTYPE(c_int)(private_addr2)
    read_rtl_sdr_samples.argtypes=[c_void_p]
    close_rtlsdr = ctypes.CFUNCTYPE(c_int)(private_addr3)
    close_rtlsdr.argtypes = [c_int]

    change_setting = ctypes.CFUNCTYPE(c_int)(private_addr4)
    change_setting.argtypes = [c_char_p]


def setting_change(setting_params):
    """
    update RTL-SDR setting for scanning
    """
    global rtl_device
    global init_rtl_sdr
    if rtl_device is not None:
        change_setting(setting_params.encode("ascii"))

def init_device(setting_params,gain=50,interval=1):
    """
    init C level RTL-SDR library and load device
    :param setting_params:
    :param gain:
    :param interval:
    :return:
    """
    global rtl_device
    global init_rtl_sdr
    init_rtl_sdr(setting_params.encode("ascii"), 40, 0.1, 0.1)
    rtl_device = True

def read_samples(duration):
    """
    read RTL-POWER samples
    """
    global read_rtl_sdr_samples,buffer
    old = time.time()
    buffer = []
    while time.time() - old < duration:
        read_rtl_sdr_samples(py_callback)
        time.sleep(0.000000000000001)
    return buffer

def close_device():
    """
    close C level RTL-POWER library and release device
    """
    global rtl_device
    global close_rtlsdr
    close_rtlsdr(1)
    rtl_device = False


if __name__ == "__main__":
    load_lib()
    init_device("100M:200M:195k")
    print(read_samples(0.1))
    close_device()

