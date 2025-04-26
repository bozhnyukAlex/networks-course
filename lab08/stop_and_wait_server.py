import socket
import random
import time
import os

class StopAndWaitServer:
    def __init__(self, host='127.0.0.1', port=5001, loss_rate=0.3, buffer_size=1024):
        self.host = host
        self.port = port
        self.loss_rate = loss_rate
        self.buffer_size = buffer_size
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.expected_seq_num = 0

    def simulate_packet_loss(self):
        return random.random() < self.loss_rate

    def receive_packet(self):
        try:
            data, addr = self.socket.recvfrom(self.buffer_size)
            return data, addr
        except socket.timeout:
            return None, None
        
    def send_ack(self, seq_num, addr):
        if self.simulate_packet_loss():
            print(f"Server Log: Simulating ACK loss for packet {seq_num}")
            return

        ack = str(seq_num).encode()
        self.socket.sendto(ack, addr)
        print(f"Server Log: Sent ACK {seq_num}")

    def run(self, output_filename="received_file.txt"):
        print("Server Log: Server started, waiting for packets...")
        received_data = bytearray()
        try:
            while True:
                packet, addr = self.receive_packet()
                if packet:
                    seq_num = int(packet[:1].decode())
                    data = packet[1:]
                    
                    if self.simulate_packet_loss():
                        print(f"Server Log: Simulating loss of packet {seq_num}")
                        continue

                    if seq_num == self.expected_seq_num:
                        print(f"Server Log: Received packet {seq_num} with {len(data)} bytes")
                        received_data.extend(data)
                        self.send_ack(seq_num, addr)
                        self.expected_seq_num = 1 - self.expected_seq_num  # Toggle between 0 and 1
                    else:
                        print(f"Server Log: Received out-of-order packet {seq_num}, expected {self.expected_seq_num}")
                        self.send_ack(1 - self.expected_seq_num, addr) #send previous ack
                
        except KeyboardInterrupt:
            print("Server Log: Server interrupted")
        finally:
            with open(output_filename, "wb") as f:
                f.write(received_data)
            print(f"Server Log: File received successfully and saved to {output_filename}")
            self.socket.close()


if __name__ == "__main__":
    server = StopAndWaitServer(loss_rate=0.3)
    server.run()