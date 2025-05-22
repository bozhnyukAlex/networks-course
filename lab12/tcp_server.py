import tkinter as tk
from tkinter import messagebox
import socket
import struct
import time
import threading


class DataReceiver:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def listen(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.bind((self.host, self.port))
                server.listen()
                connection, address = server.accept()
                with connection:
                    data = connection.recv(4)
                    N = struct.unpack('>I', data)[0]
                    start = time.time()
                    total = 0
                    for _ in range(N):
                        packet = connection.recv(1024)
                        if not packet:
                            break
                        total += len(packet)
                    duration = time.time() - start
                    rate = total / duration if duration > 0 else 0
                    return rate, N, None
        except Exception as e:
            return None, None, str(e)


class Interface:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TCP Receiver")
        self.default_ip = "127.0.0.1"
        self.default_port = "8080"
        self.speed_text = tk.StringVar(value="0 B/s")
        self.packets_text = tk.StringVar(value="0 of 0")
        self.create_ui()
        self.root.mainloop()

    def create_ui(self):
        tk.Label(self.root, text="Listening IP").pack()
        self.ip_input = tk.Entry(self.root)
        self.ip_input.insert(0, self.default_ip)
        self.ip_input.pack()
        
        tk.Label(self.root, text="Listening Port").pack()
        self.port_input = tk.Entry(self.root)
        self.port_input.insert(0, self.default_port)
        self.port_input.pack()
        
        tk.Label(self.root, text="Transfer Speed").pack()
        tk.Label(self.root, textvariable=self.speed_text).pack()
        
        tk.Label(self.root, text="Packets Received").pack()
        tk.Label(self.root, textvariable=self.packets_text).pack()
        
        self.start_button = tk.Button(self.root, text="Start", command=self.start_listening)
        self.start_button.pack()

    def start_listening(self):
        self.start_button.config(state="disabled")
        ip = self.ip_input.get()
        try:
            port = int(self.port_input.get())
            if not 0 < port < 65536:
                raise ValueError("Port must be between 1 and 65535")
        except ValueError as ve:
            messagebox.showerror("Invalid Input", str(ve))
            self.start_button.config(state="normal")
            return

        receiver = DataReceiver(ip, port)
        thread = threading.Thread(target=self.run_receiver, args=(receiver,))
        thread.start()

    def run_receiver(self, receiver):
        speed, packets, error = receiver.listen()
        if error:
            self.root.after(0, messagebox.showerror, "Error", error)
        else:
            self.root.after(0, self.update_display, speed, packets)
        self.root.after(0, self.start_button.config, {"state": "normal"})

    def update_display(self, speed, total):
        self.speed_text.set(f"{speed:.2f} B/s")
        self.packets_text.set(f"{total} of {total}")


if __name__ == "__main__":
    Interface()