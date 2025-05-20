import socket
import threading
import time
import random

class GBNServer:
    def __init__(self, host='127.0.0.1', port=12345, window_size=4, timeout=1):
        self.host = host
        self.port = port
        self.window_size = window_size
        self.timeout = timeout       
        self.packet_size = 1024
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.next_seq_num = 0
        self.base = 0
        self.expected_seq_num = 0
        self.received_data = {}
        self.lock = threading.Lock()
        self.file_name = "received_file.txt"        
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2048*2)

    def log(self, message):
        print(f"Server Log: {message}")

    def send_ack(self, seq_num, addr):
        ack_size = len(str(seq_num).encode())
        self.log(f"Sending ACK for packet: {seq_num}")
        self.sock.sendto(str(seq_num).encode(), addr)        
        self.log(f"Ack size sent: {ack_size}")

    def receive_packet(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(self.packet_size)
                self.log(f"Packet size received: {len(data)}")
                packet = data.decode()
                
                                
                seq_num, packet_data = packet.split(":", 1)
                seq_num = int(seq_num)
                
                if seq_num == self.expected_seq_num:
                    
                    self.log(f"Received packet: {seq_num}")
                    self.received_data[seq_num] = packet_data
                    self.expected_seq_num += 1
                    self.send_ack(self.expected_seq_num-1, addr)                    
                else:
                    self.log(f"Out-of-order packet received: {seq_num}, expected {self.expected_seq_num}")
                    self.send_ack(self.expected_seq_num - 1, addr)
            except Exception as e:
                self.log(f"Error receiving packet: {e}")
                

    def save_data_to_file(self):
        with open(self.file_name, "w") as f:
            for i in sorted(self.received_data.keys()):
                f.write(self.received_data[i])

    def print_window_status(self):
        window_status = [f"[{i}]" if i < self.expected_seq_num else "[ ]" for i in range(self.expected_seq_num-self.window_size, self.expected_seq_num)]
        self.log(f"Window Status: {window_status}")


    def start(self):
        self.log("Server started.")
        try:
          receive_thread = threading.Thread(target=self.receive_packet)
          receive_thread.daemon = True
          receive_thread.start()
          while True:
            time.sleep(0.5)
            self.print_window_status()
            if self.expected_seq_num > 0 and len(self.received_data) == self.expected_seq_num :
                self.save_data_to_file()
                self.log("All data received. Saving to file.")
                break
        except KeyboardInterrupt:
            self.log("Server shutting down.")
        finally:
            self.sock.close()


if __name__ == "__main__":
    server = GBNServer()
    server.start()