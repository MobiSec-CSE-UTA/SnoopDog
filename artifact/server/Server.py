import socket
import threading
import time
from multiprocessing import Process

from BaitPacketTransmitter import BaitPacketTransmitter
import pathlib

data_file_path = ""
DATA_PATH = pathlib.Path().resolve()

class SessionHandler:
    """
    Common util for TCP/UDP session handling
    please see handle_session
    """
    def __init__(self, client_socket, client_address):
        self.file_server = None
        self.client_socket:socket.socket = client_socket
        self.client_address = client_address
        self.trans = BaitPacketTransmitter(client_address[0],client_address[1])
        self.buffer_estimation_history = {}

    def decomposeMessage(self,origin:str):
        return origin.split(",")

    def handle_session(self):
        """
        Coordinating Host PC with the Detector simultaneously
        """
        while True:
            recvBytes = self.client_socket.recv(4)
            plength = int.from_bytes(recvBytes,'little')
            packet = self.client_socket.recv(plength)
            cmd = int.from_bytes(packet[0:4],'little')
            message = packet[4:plength].decode("utf-8")
            if len(message) == 0:
                signalID = -1
            else:
                if "," in message:
                    signalID = int(message.split(",")[0])
                    message = message[message.index(",")+1:]
                else:
                    signalID = int(message)
            if cmd == 5:
                small_pattern = message
                self.sendCMD(cmd + 1, str(signalID))
                self.pattern_matching(signalID,small_pattern=small_pattern)
            else:
                time.sleep(0.1)

    def close(self):
        self.client_socket.close()
        self.file_server.close_server()
    

    def pattern_matching(self,signalID = 0,small_pattern="5.0,5.0"):
        self.buffer_estimation_history[signalID] = 1
        self.trans.bait_signal_transmission(small_pattern, 480)
        return

    def sendCMD(self,cmd:int,message:str):
        c_data = cmd.to_bytes(4,"little")
        m_data = message.encode("utf-8")
        b_data = c_data+m_data
        b_data_length = len(b_data)
        r_data = b_data_length.to_bytes(4,"little") + b_data
        self.client_socket.send(r_data)

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Server listening on {self.host}:{self.port}")
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
            session_handler = SessionHandler(client_socket, client_address)
            session_thread = threading.Thread(target=session_handler.handle_session)
            session_thread.start()

    def stop(self):
        self.server_socket.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Server for SnoopDog")

    parser.add_argument("--port", "-p", type=int, required=True, help="Port for control a bait traffic")

    args = parser.parse_args()

    SERVER_IP = ''
    SERVER_PORT = args.port

    server = Server(SERVER_IP,SERVER_PORT)

    try:
        server.start()
    except KeyboardInterrupt as e:
        print("Ctrl - C, Stoping Server...")
        server.stop()