!/bin/bash

echo 'For benign device 1'
echo 'target data file to load = ./recorded_data/benign1.data'
python3 snoopdog_detector.py --data ./recorded_data/benign1.data

echo 'For benign device 2'
echo 'target data file to load = ./recorded_data/benign2.data'
python3 snoopdog_detector.py --data ./recorded_data/benign2.data

echo 'For malicious sniffer 1'
echo 'target data file to load = ./recorded_data/malicious1.data'
python3 snoopdog_detector.py --data ./recorded_data/malicious1.data

echo 'For malicious sniffer 2'
echo 'target data file to load = ./recorded_data/malicious2.data'
python3 snoopdog_detector.py --data ./recorded_data/malicious2.data
