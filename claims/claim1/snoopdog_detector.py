import fastdtw
import numpy as np
import scipy.signal as sps


du = 5
num_of_fold = 2


class usbEavesdropperDetector:
    def __init__(self):
        self.rtl_time = 0.0
        self.num_of_fold = 2

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
    
    def back_to_power(self, x):
        s1_delog = x / 10.
        s1_delog = np.power(10, s1_delog)
        return s1_delog
    
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

        # do sum all frequency
        s1_power_sum_freq = np.mean(s1_power, axis=1)

        # do folding signal following traffic pattern, only traffic activated part will be folded.
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
        #do DTW distance test, if lower then 3 then it is malicious.
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
    import pickle
    parser = argparse.ArgumentParser(description="Detector test code with data")
    parser.add_argument("--data", "-d", type=str, required=False, help="Data file to test",default=None)

    args = parser.parse_args()
    data = None
    if not args.data:
        print("No data file is designated. please specify the data file to test.")
        print("Recorded EM signal data of ")
        print("1. Malicious device")
        print("2. Benign device data")
        i = int(input("Enter your choice: "))
        if i == 1:
            data = "./recorded_data/malicious2.data"
        elif i == 2:
            data = "./recorded_data/benign2.data"
            pass
    else:
        data = args.data

    s_data = None
    print("target data file to load = ",data)
    with open(data, "rb") as f:
        s_data = pickle.load(f)

    g_predefined_interval_data = s_data["interval"]
    num_of_fold = s_data["num_of_fold"]
    raw_signal  = s_data["data"]
    print(f"{num_of_fold} fold record data has been loaded.")

    d = usbEavesdropperDetector()
    f1,s1 =d.refine_signal(raw_signal)
    result = d.analyze_and_detect(s1, f1, g_predefined_interval_data, num_of_fold)
    print("Detection result\t: ",result[0])
    print("DTW distance\t\t: ",result[1])