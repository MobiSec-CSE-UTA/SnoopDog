import socket
import threading
import time


# default pattern
iii = 5
g_predefined_interval_data = [(iii,iii)] * 2
g_predefined_interval_data.insert(0, (0, iii))
g_predefined_interval_data.append((0, iii))

class BaitPacketTransmitter():
    """
    This pertains to transmission of bait traffic from the Host PC on the USB Bus.
    """
    mode_dumping = 0
    mode_pattern = 0
    packet_size = 512*2

    def __init__(self, address: str, port: int):
        self.mode = self.mode_dumping
        self.bait_packet_data = None
        self.signal_pattern_length = None
        self.signal_pattern_index = None
        self.signal_pattern = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = (address, port)
        self.onProcessing = False
        self.make_bait_packet_data()
    def make_bait_packet_data(self):
        self.bait_packet_data = ("1" * self.packet_size).encode("ascii")

    def bait_signal_transmission(self, predefined_interval_data=None, target_mbps=80):
        if predefined_interval_data is None:
            predefined_interval_data = g_predefined_interval_data
        else:
            inter = predefined_interval_data.split(",")
            print([(float(inter[0]),float(inter[1]))])
            predefined_interval_data = [(float(inter[0]),float(inter[1]))]
        self.generate_udp_traffic(target_mbps,predefined_interval_data)

    def generate_udp_traffic(self, target_mbps, traffic_pattern):
        """
        Generate traffic following USB traffic 
        """
        # Parameters for sending traffic
        PACKET_SIZE = 1500  # bytes
        RATE_MBPS = target_mbps  # Mbps
        BYTES_PER_SECOND = (RATE_MBPS * 1_000_000) // 8
        PACKETS_PER_SECOND = BYTES_PER_SECOND // PACKET_SIZE
        INTERVAL = 1 / PACKETS_PER_SECOND

        # Making the individual packets of Bait Traffic
        def send_udp_packets():
            packet = bytearray(0x31 for _ in range(PACKET_SIZE))
            for duration_on, duration_off in traffic_pattern:
                # Send packets for duration_on
                end_time = time.perf_counter() + duration_on
                # busting pattern
                while time.perf_counter() < end_time:
                    packet_start_time = time.perf_counter()
                    # All packet will be dropped by detector following network device control in it.
                    self.sock.sendto(packet, ("192.168.7.2",5055))
                    elapsed_time = time.perf_counter() - packet_start_time
                    # Wait for duration_off
                    while elapsed_time < INTERVAL:
                        elapsed_time = time.perf_counter() - packet_start_time
                end_time = time.perf_counter() + duration_off
                a = 0
                
                while time.perf_counter() < end_time:
                    a+=1
        
        # Multi-threading for continuous operation
        traffic_thread = threading.Thread(target=send_udp_packets)
        traffic_thread.daemon = True
        traffic_thread.start()
        traffic_thread.join()



    def stop_transmission(self):
        self.onProcessing = False
