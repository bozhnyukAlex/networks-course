import tkinter as tk
from tkinter import messagebox
import socket
import struct
import time
import threading


class PacketReceiver:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def listen(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.bind((self.host, self.port))
                s.settimeout(2)
                data, _ = s.recvfrom(4)
                N = struct.unpack('>I', data)[0]
                received = set()
                start = None
                
                while True:
                    try:
                        packet, _ = s.recvfrom(1024)
                        if start is None:
                            start = time.time()
                        seq = struct.unpack('>I', packet[:4])[0]
                        received.add(seq)
                    except socket.timeout:
                        break
                
                elapsed = time.time() - start if start else 0
                bytes_total = len(received) * 1020
                kb_speed = (bytes_total / elapsed) / 1000 if elapsed > 0 else 0
                return kb_speed, len(received), N, None
        except Exception as e:
            return 0, 0, 0, str(e)


class AppInterface:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("UDP Receiver")
        self.default_ip = "127.0.0.1"
        self.default_port = "8888"
        self.speed_text = tk.StringVar(value="0 KB/s")
        self.packet_text = tk.StringVar(value="0 of 0")
        self.create_layout()
        self.root.mainloop()

    def create_layout(self):
        tk.Label(self.root, text="Listen IP").pack()
        self.ip_field = tk.Entry(self.root)
        self.ip_field.insert(0, self.default_ip)
        self.ip_field.pack()
        
        tk.Label(self.root, text="Listen Port").pack()
        self.port_field = tk.Entry(self.root)
        self.port_field.insert(0, self.default_port)
        self.port_field.pack()
        
        tk.Label(self.root, text="Transfer Speed").pack()
        tk.Label(self.root, textvariable=self.speed_text).pack()
        
        tk.Label(self.root, text="Packets Received").pack()
        tk.Label(self.root, textvariable=self.packet_text).pack()
        
        self.start_btn = tk.Button(self.root, text="Start", command=self.initiate_listen)
        self.start_btn.pack()

    def initiate_listen(self):
        self.start_btn.config(state="disabled")
        ip = self.ip_field.get()
        port_str = self.port_field.get()
        
        try:
            port_val = int(port_str)
            if not 0 < port_val < 65536:
                raise ValueError("Port must be 1-65535")
        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve))
            self.start_btn.config(state="normal")
            return
        
        receiver = PacketReceiver(ip, port_val)
        threading.Thread(target=self.run_receiver, args=(receiver,)).start()

    def run_receiver(self, receiver):
        speed, count, total, error = receiver.listen()
        if error:
            self.root.after(0, messagebox.showerror, "Error", error)
        else:
            self.root.after(0, self.update_view, speed, count, total)
        self.root.after(0, self.start_btn.config, {"state": "normal"})

    def update_view(self, speed, current, max_val):
        self.speed_text.set(f"{speed:.2f} KB/s")
        self.packet_text.set(f"{current} of {max_val}")


if __name__ == "__main__":
    AppInterface()