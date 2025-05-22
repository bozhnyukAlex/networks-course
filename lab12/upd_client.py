import tkinter as tk
from tkinter import messagebox
import socket
import struct
import os
import threading


class PacketSender:
    def __init__(self, host, port, count):
        self.host = host
        self.port = port
        self.count = count

    def send(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(struct.pack('>I', self.count), (self.host, self.port))
                for i in range(self.count):
                    header = struct.pack('>I', i)
                    payload = os.urandom(1020)
                    s.sendto(header + payload, (self.host, self.port))
            return True, "Packets sent successfully"
        except Exception as e:
            return False, str(e)


class SenderUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("UDP Sender")
        self.default_ip = "127.0.0.1"
        self.default_port = "8888"
        self.default_count = "5"
        self.create_ui()
        self.root.mainloop()

    def create_ui(self):
        tk.Label(self.root, text="Receiver IP").pack()
        self.ip_entry = tk.Entry(self.root)
        self.ip_entry.insert(0, self.default_ip)
        self.ip_entry.pack()

        tk.Label(self.root, text="Receiver Port").pack()
        self.port_entry = tk.Entry(self.root)
        self.port_entry.insert(0, self.default_port)
        self.port_entry.pack()

        tk.Label(self.root, text="Packets to send").pack()
        self.count_entry = tk.Entry(self.root)
        self.count_entry.insert(0, self.default_count)
        self.count_entry.pack()

        self.send_button = tk.Button(self.root, text="Send", command=self.prepare_send)
        self.send_button.pack()

    def prepare_send(self):
        self.send_button.config(state="disabled")
        ip = self.ip_entry.get()
        port = self.port_entry.get()
        count = self.count_entry.get()

        try:
            port_num = int(port)
            count_num = int(count)
            if not 0 < port_num < 65536:
                raise ValueError("Port must be 1-65535")
            if count_num <= 0:
                raise ValueError("Count must be positive")
        except ValueError as ve:
            messagebox.showerror("Error", str(ve))
            self.send_button.config(state="normal")
            return

        sender = PacketSender(ip, port_num, count_num)
        threading.Thread(target=self.run_sender, args=(sender,)).start()

    def run_sender(self, sender):
        result, message = sender.send()
        self.root.after(0, self.handle_result, result, message)

    def handle_result(self, success, message):
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)
        self.send_button.config(state="normal")


if __name__ == "__main__":
    SenderUI()