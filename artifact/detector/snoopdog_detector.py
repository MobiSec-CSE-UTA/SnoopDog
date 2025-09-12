import socket
import time
import fastdtw
import client
from pyrtl_power import init_device, read_samples, close_device, load_lib
from copy import deepcopy
import numpy as np
import scipy.signal as sps

cli = None

du = 5
num_of_fold = 2


class usbEavesdropperDetector:

    def __init__(self, server_address: tuple,with_rtl_sdr = True):
        self.sock = None
        self.server_ip = server_address[0]
        self.server_port = server_address[1]
        self.rtl_time = 0.0
        self.load_lib_status = False
        self.num_of_fold = 2
        self.with_rtl_sdr = with_rtl_sdr
        if with_rtl_sdr:
            load_lib()

    def __del__(self):
        if self.load_lib_status:
            close_device()

    def readRtl(self, duration=.5):
        return read_samples(duration)

    def connect_to_server(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.server_ip, self.server_port))
        self.cli = client.SessionHandler(self.sock)

    def decision_make_dtw(final_result_siganl, pattern, threshold):
        distance, path = fastdtw.fastdtw(final_result_siganl, pattern, dist=2)
        return distance < threshold, distance

    def start_pattern_matching(self, fold_pattern, num_of_fold):
        self.num_of_fold = num_of_fold
        # init RTL-SDR device with scanning frequency range.
        init_device(setting_params="100M:200M:195k")
        # pattern is traffic pattern, based on this fold will work.
        pattern = fold_pattern
        # before a bait traffic, record one background signal.
        base_line_signal = deepcopy(self.readRtl(0.01))
        # wait some while
        time.sleep(0.5)
        collected_signal = []
        [collected_signal.append(i) for i in base_line_signal]
        # copy collected backgraound and copy it to python list.
        collected_signal[-1].append([time.time()])
        # request real patterned traffic.
        for i, s in pattern:
            length_siganl = i + s
            self.cli.start_pattern_matching(f_size="%3.3f,%3.3f" % (i, s))
            while length_siganl > 0:
                p = time.time()
                # record EM siganl.
                reading = self.readRtl(.01)
                [collected_signal.append(i) for i in reading]
                length_siganl -= (time.time() - p)

        # return collected signal
        return collected_signal

    def back_to_power(self, x):
        s1_delog = x / 10.
        s1_delog = np.power(10, s1_delog)
        return s1_delog

    def extend_signal(self, signal, target_length):
        target_length = np.ceil(target_length)
        target_length = int(target_length)
        ratio = target_length / signal.shape[0]
        recovered_signal = np.ones((target_length, signal.shape[1])) * -1
        for i in range(0, signal.shape[0], 1):
            new_idx = i * ratio
            n_i = int(new_idx)
            recovered_signal[n_i, ...] = signal[i, ...]
        if ratio > 1.:
            for i in range(0, recovered_signal.shape[0], 1):
                if recovered_signal[i, 0] == -1:
                    recovered_signal[i, ...] = recovered_signal[i - 1, ...]
        return recovered_signal

    def folding_times_on_signal(self, signal_original, pattern):
        """
        fold signal only for traffic pattern part on signal.
        :param signal_original: collected EM signal
        :param pattern: traffic pattern
        :return: folded signal
        """
        signal = signal_original.copy()
        preamble = pattern[0]
        postamble = pattern[-1]
        folded_result_length = int(np.ceil(sum([pattern[1][0]])))
        folded_result = np.zeros(shape=(int(np.ceil(sum([pattern[1][0]], )))))
        folding_indies = [int(np.ceil(sum(preamble)))]
        g_predefined_interval_string = []
        for i in pattern:
            for ii in range(0, int(np.ceil(i[0]))):
                g_predefined_interval_string.append(1)
            for ii in range(0, int(np.ceil(i[1]))):
                g_predefined_interval_string.append(0)
        for i in pattern[1:len(pattern) - 1]:
            folding_indies.append(int(np.ceil((i[0]))) + int(np.ceil((i[1]))) + folding_indies[-1])
        for i in folding_indies[0:len(folding_indies) - 1]:
            folded_result = folded_result + signal[i:i + folded_result_length]
        return np.hstack([signal[0:int(np.ceil(sum(preamble)))], folded_result, signal[-int(np.ceil(sum(postamble))):]])

    def refine_signal(self, signal_data):
        """
        original signal structure : [(signal data,frequency label),(signal data,frequency label), ....]
        reorganized signal structure : [signal data,signal data,signal data,...],[frequency label,frequency label,...]
        """
        signal_data = signal_data
        result_signal = []
        result_requency_label = []
        for i in range(0, len(signal_data)):
            header = signal_data[i][0]
            data = signal_data[i][1]
            frequency_labels = []
            for i1 in range(0, header.shape[0], 5):
                l_f = header[i1 + 0]
                h_f = header[i1 + 1]
                interval_f = header[i1 + 2]
                f_array = np.arange(l_f, h_f + interval_f, interval_f)
                frequency_labels.append(f_array)
            f_lables = np.hstack(frequency_labels)
            result_signal.append(data)
            result_requency_label.append(f_lables)
        return np.vstack(result_requency_label), np.vstack(result_signal)

    def convert_bait_traffic_signal_as_nparray(self, signal):
        """
        Simple function to convert bait traffic
        if pattern is [(5,0),(0,5))
        then make that as 1D array: [1,1,1,1,1,0,0,0,0,0]
        """
        bait_traffic_signal = []
        for i, ii in signal:
            for a in range(0, int(np.ceil(i))):
                bait_traffic_signal.append(1)
            for a in range(0, int(np.ceil(ii))):
                bait_traffic_signal.append(0)
        bait_traffic_signal = np.array(bait_traffic_signal)
        return bait_traffic_signal

    def analyze_and_detect(self, s1, f1, g_predefined_interval_data, num_of_fold):
        """
        :param s1: collected signal from RTL-SDR
        :param f1: collected signal's frequency label from RTL-SDR
        :param g_predefined_interval_data: bait traffic pattern
        :param num_of_fold: how many folds.
        :return: True: malicious device detected. False: malicious device not detected
        """
        s1_original = s1

        # take first and last signal as collected background, this is will be used for removal of background.
        s1_background = (s1_original[0, ...] + s1_original[-1, ...]) / 2.

        #appliy wiener filter
        s1_denoised = sps.wiener(s1_original)
        # remove background noise
        s1_denoised = s1_denoised - s1_background

        # take average of first two and last 5 samples to use them as rho calculation which is for pattern recovery
        s1_background = s1_denoised[1, ...] + s1_denoised[2, ...] + s1_denoised[-4, ...] + s1_denoised[-3, ...] + \
                        s1_denoised[-2, ...] + s1_denoised[-1, ...]
        s1_background = s1_background / 6.

        #Cut first background which is not in the pattern.
        s1_original = s1_denoised[1:, ...]

        #make bait traffic pattern into np.ndarray to easy calculation.
        bait_traffic_signal = self.convert_bait_traffic_signal_as_nparray(g_predefined_interval_data)

        # make collected signal length same as traffic pattern length by stretching it.
        s1 = self.extend_signal(s1_original, bait_traffic_signal.shape[0])

        #convert log signals to power signals
        s1_power = self.back_to_power(s1)
        s1_background = self.back_to_power(s1_background)

        
        # do folding signal following traffic pattern, only traffic cotaining bait packets will be folded.
        s1_power_sum_freq = np.mean(s1_power, axis=1)
        folded_result_h = self.folding_times_on_signal(s1_power_sum_freq,
                                                       g_predefined_interval_data)
        # use same procedure but on traffic pattern, the traffic pattern will be folded means that
        # only one repeated traffic pattern remained.
        folded_pattern_h = self.folding_times_on_signal(bait_traffic_signal,
                                                        g_predefined_interval_data)
        folded_pattern_h[np.where(folded_pattern_h >= 1.)] = 1.

        #calculate rho which is explained in the paper
        multiplier = num_of_fold
        rho_back = multiplier * (np.mean(s1_background) + 2*np.std(s1_background))

        folded_signal_h = np.ones(shape=folded_result_h.shape)
        folded_signal_h[np.where(folded_result_h < rho_back)] = 0
        #do DTW distance test, if lower than 3 then it is malicious.
        result_dtw = self.decision_make_dtw(folded_signal_h, folded_pattern_h, 3)
        return result_dtw



    def decision_make_dtw(self, final_result_siganl, pattern, threshold):
        """
        make a decision with DTW testing, if DTW distance is lower than threshold, then the scanned device is emitting
        a signal following bait traffic signal.
        """
        distance, path = fastdtw.fastdtw(final_result_siganl, pattern, dist=2)
        return distance < threshold, distance


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Detector for SnoopDog")

    parser.add_argument("--ip", "-i", type=str, required=True, help="Ip address of Host PC")
    parser.add_argument("--port", "-p", type=int, required=True, help="Port for control a bait traffic")

    SERVER_IP = "192.168.7.15"
    SERVER_PORT = 5050

    args = parser.parse_args()
    if args.ip:
        SERVER_IP = args.ip
    if args.port:
        SERVER_PORT = args.port

    # fold signal duration setting
    g_predefined_interval_data = [(du, du)] * num_of_fold
    g_predefined_interval_data.insert(0, (0, du))
    g_predefined_interval_data.append((0, du))

    d = usbEavesdropperDetector((SERVER_IP, SERVER_PORT),with_rtl_sdr=True)

    # connect to Host PC
    d.connect_to_server()

    # request bait traffic and record EM signal
    collected_signal = d.start_pattern_matching(g_predefined_interval_data, num_of_fold)
    # Reorganize data structure
    f1, s1 = d.refine_signal(collected_signal)
    # analyze signal and make a detection result
    result = d.analyze_and_detect(s1, f1, g_predefined_interval_data, num_of_fold)
    print("detection results:", result)  # if malicious detected then True.
