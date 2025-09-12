import pickle
from detector import usbEavesdropperDetector
import argparse


if __name__ == "__main__":

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

    d = usbEavesdropperDetector(('',0),with_rtl_sdr=False)
    f1,s1 =d.refine_signal(raw_signal)
    result = d.analyze_and_detect(s1, f1, g_predefined_interval_data, num_of_fold)
    print("Detection result :",result[0])
    print("\tDTW distance:",result[1])