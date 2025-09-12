import socket
import random

class SessionHandler:
    """
    handle session communication with Host PC
    send / receive commands
    """
    def __init__(self, sock):
        self.sock:socket.socket = sock
        self.buffer_estimation_history = {}
        self.signalID_histories = []

    def start_pattern_matching(self,SignalID = None,size_ = "9,6"):
        CMD = 5
        if SignalID == None:
            id = random.randint(1, 100000)
            self.signalID_histories.append(id)
        self.sock.send(self.compose_message(CMD,message=str(size_)))
        recv_msg = self.wait_for_respond(CMD+1)
        if recv_msg is None:
            print("Error on communication")
            return
        if int(recv_msg[0]) not in self.signalID_histories:
            print("Communication Error check procedure")
            print("message : ", recv_msg)
            print("last signalID : ", self.signalID_histories[-1])
        return


    def compose_message(self, CMD: int, message: str = None):
        b_cmd = CMD.to_bytes(4, "little")
        id = self.signalID_histories[-1]
        b_id = str(id).encode("utf-8")
        if message != None:
            b_message = (","+message).encode("utf-8")
            b_id = b_id + b_message
        message = b_cmd + b_id
        b_length = len(message).to_bytes(4, "little")
        message = b_length + message
        return message

    def wait_for_respond(self,estimated_CMD:int):
        b_length = self.sock.recv(4)
        length = int.from_bytes(b_length,"little")
        b_message = self.sock.recv(length)
        b_CMD = b_message[:4]
        recieved_CMD = int.from_bytes(b_CMD,"little")
        message = b_message[4:].decode("utf-8")
        received_message = message.split(",")
        if recieved_CMD != estimated_CMD:
            print("Communication Error check procedure")
            print("message : ",message)
        return received_message

    def close(self):
        self.sock.close()



