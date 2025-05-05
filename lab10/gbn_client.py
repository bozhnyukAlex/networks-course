import socket
import time
import threading

class GBNClient:
    def __init__(self, server_address, server_port, filename, window_size, timeout):
        self.server_address = server_address
        self.server_port = server_port
        self.filename = filename
        self.window_size = window_size
        self.timeout = timeout   
        self.packet_size = 512
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.base = 0
        self.next_seq_num = 0
        self.packets = []
        self.acks = []
        self.lock = threading.Lock()
        self.timers = {}

    def create_packets(self, data):
        for i in range(0, len(data), self.packet_size):
            self.packets.append(data[i:i + self.packet_size])

    def send_packet(self, seq_num, packet):
        packet_with_seq = str(seq_num).encode() + b":" + packet        
        self.socket.sendto(packet_with_seq, (self.server_address, self.server_port))
        packet_size = len(packet_with_seq)        
        print(f"Sending packet {seq_num}, size: {packet_size} bytes")


    def start_timer(self, seq_num):
        timer = threading.Timer(self.timeout, self.handle_timeout, [seq_num])
        timer.start()
        self.timers[seq_num] = timer

    def stop_timer(self, seq_num):
        if seq_num in self.timers:
            self.timers[seq_num].cancel()
            del self.timers[seq_num]

    def handle_timeout(self, seq_num):
        with self.lock:
            if seq_num >= self.base and seq_num < self.next_seq_num :
              print(f"Timeout, resending packets from {self.base}")
              for i in range(self.base, self.next_seq_num):
                  if i < len(self.packets):
                       self.send_packet(i,self.packets[i])
                       self.start_timer(i)
    
    def receive_ack(self):
       while self.base < len(self.packets):
           try:
              self.socket.settimeout(1)
              ack_data, _ = self.socket.recvfrom(1024)
              ack_seq_num = int(ack_data.decode())
              ack_size = len(ack_data)
              with self.lock:                  
                  print(f"Received ACK {ack_seq_num}, size: {ack_size} bytes")

                 
                  self.stop_timer(ack_seq_num)
                  self.acks.append(ack_seq_num)
                  if ack_seq_num == self.base:
                      self.base += 1
                      while self.base < len(self.packets) and self.base in self.acks:
                          self.base += 1
                  
                  
                  window_status = f"Window Status: ["                  
                  for i in range(self.base, min(self.base + self.window_size, len(self.packets))):                    
                      window_status += f"{i} "
                  window_status += "]"
                  print(window_status)        
                  
           except socket.timeout:
              pass

    def run(self):
        try:
            with open(self.filename, "rb") as file:
                data = file.read()
            self.create_packets(data)

            receiver_thread = threading.Thread(target=self.receive_ack)
            receiver_thread.daemon = True
            receiver_thread.start()

            while self.base < len(self.packets):
                with self.lock:
                    while self.next_seq_num < self.base + self.window_size and self.next_seq_num < len(self.packets):
                        self.send_packet(self.next_seq_num, self.packets[self.next_seq_num])
                        self.start_timer(self.next_seq_num)
                        self.next_seq_num += 1
                time.sleep(0.01)
            receiver_thread.join()
            print("Packet sent successfully")

        except FileNotFoundError:
            print(f"Error: File '{self.filename}' not found.")
        finally:
            self.socket.close()


if __name__ == "__main__":
    server_address = "127.0.0.1"
    server_port = 12345   
    filename = "data.txt"
    timeout = 0.5 
    with open(filename, 'w') as f:
        f.write('a' * 5000)
    with open(filename, "rb") as file:       
      data = file.read()

    packets_count = (len(data) + 1024 - 1) // 1024   
    window_size = min(5, packets_count)

    client = GBNClient(server_address, server_port, filename,window_size, timeout)
    client.run()
