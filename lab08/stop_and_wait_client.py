import socket
import time
import random
import sys

class StopAndWaitClient:
    def __init__(self, server_address, server_port, filename, packet_size, timeout, loss_rate):
        self.server_address = server_address 
        self.server_port = server_port
        self.filename = filename
        self.packet_size = packet_size
        self.timeout = timeout
        self.loss_rate = loss_rate
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(self.timeout)
        self.client_seq_num = 0
        self.server_seq_num = 0
        self.last_ack_received = -1
        

    def simulate_packet_loss(self):
        return random.random() < self.loss_rate

    def send_packet(self, packet):
        if not self.simulate_packet_loss():
            try:
                self.sock.sendto(packet, (self.server_address, self.server_port))
                print(f"Client Log: Sending packet: {packet[:10]}... (Client Seq: {self.client_seq_num}, Server Ack: {self.last_ack_received})")
                return True
            except Exception as e:
                print(f"Client Log: Error sending packet: {e}")
                return False
        else:
            print(f"Client Log: Packet loss simulated (send): {packet[:10]}... (Client Seq: {self.client_seq_num}, Server Ack: {self.last_ack_received})")
            return False

    def receive_packet(self):
        try:
            data, _ = self.sock.recvfrom(self.packet_size)
            return data
        except socket.timeout:
            print("Client Log: Timeout waiting for packet")
            return None
        except Exception as e:
            print(f"Client Log: Error receiving packet: {e}")
            return None

    def run_client_send(self):
        try:
            with open(self.filename, "rb") as f:
                while True:
                    data = f.read(self.packet_size - 1)
                    if not data:
                        print("Client Log: File sent successfully.")
                        break
                    
                    packet = f"{self.client_seq_num}{self.last_ack_received}{data.decode('latin-1','ignore')}".encode()

                    while True:
                        if self.send_packet(packet):
                            received_packet = self.receive_packet()
                            if received_packet:
                                if not self.simulate_packet_loss():
                                    received_ack = int(received_packet[1:2].decode())
                                    self.last_ack_received = received_ack
                                    if received_ack == self.client_seq_num:
                                        self.client_seq_num = 1 - self.client_seq_num
                                        break
                                    else:
                                        print(f"Client Log: Wrong ack. received: {received_ack}, expected {self.client_seq_num}")
                                else:
                                    print(f"Client Log: Packet loss simulated (receive): {received_packet}")
                            else:
                                print(f"Client Log: Retransmitting packet (Client Seq: {self.client_seq_num}, Server Ack:{self.last_ack_received})")
                        else:
                            print(f"Client Log: Retransmitting packet (Client Seq: {self.client_seq_num}, Server Ack: {self.last_ack_received})")

        except FileNotFoundError:
            print(f"Client Log: Error: File '{self.filename}' not found.")
        except Exception as e:
            print(f"Client Log: An error occurred: {e}")

    def run_client_receive(self):
        try:
                while True:
                    received_packet = self.receive_packet()
                    if received_packet:
                        if not self.simulate_packet_loss():
                            server_seq = int(received_packet[:1].decode())
                            self.last_ack_received = server_seq
                            data = received_packet[2:].decode()
                            if server_seq == self.server_seq_num:
                                print(f"Client Log: Message from server: {data}")
                                self.server_seq_num = 1 - self.server_seq_num
                                break
                            else:
                                print(f"Client Log: Received out-of-order packet {server_seq}, expected {self.server_seq_num}")
                        else:
                            print(f"Client Log: Packet loss simulated (receive): {received_packet}")
        except Exception as e:
            print(f"Client Log: An error occurred: {e}")



    def run(self):
        try:
            self.run_client_send()
            self.run_client_receive()
        finally:
            self.sock.close()


if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("Usage: python stop_and_wait_client.py <server_address> <server_port> <filename> <packet_size> <timeout> <loss_rate>")
        sys.exit(1)

    server_address = sys.argv[1]
    server_port = int(sys.argv[2])
    filename = sys.argv[3]
    packet_size = int(sys.argv[4])
    timeout = float(sys.argv[5])
    loss_rate = float(sys.argv[6])

    client = StopAndWaitClient(server_address, server_port, filename, packet_size, timeout, loss_rate)
    client.run()