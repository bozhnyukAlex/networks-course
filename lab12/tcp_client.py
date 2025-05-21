import tkinter as tk
from tkinter import messagebox
import socket
import struct
import os
import threading


class PacketTransmitter:
    def __init__(self, host, port, packet_count):
        self.host = host
        self.port = port
        self.packet_count = packet_count

    def transmit(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
                connection.connect((self.host, self.port))
                connection.sendall(struct.pack('>I', self.packet_count))
                
                for sequence_number in range(self.packet_count):
                    header = struct.pack('>I', sequence_number)
                    payload = os.urandom(1020)
                    packet = header + payload
                    connection.sendall(packet)
                    
            return True, "Transmission completed successfully"
            
        except ValueError as ve:
            return False, f"Invalid input: {str(ve)}"
        except socket.gaierror:
            return False, "Failed to resolve hostname"
        except socket.timeout:
            return False, "Connection timed out"
        except ConnectionRefusedError:
            return False, "Connection refused by remote host"
        except Exception as e:
            return False, f"Transmission failed: {str(e)}"


class NetworkClientGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Packet Transmission Client")
        
        self.default_ip = "127.0.0.1"
        self.default_port = "8080"
        self.default_count = "5"
        
        self.create_interface()
        self.root.mainloop()

    def create_interface(self):
        tk.Label(self.root, text="Destination IP Address").pack()
        self.ip_field = tk.Entry(self.root)
        self.ip_field.insert(0, self.default_ip)
        self.ip_field.pack()
        
        tk.Label(self.root, text="Destination Port Number").pack()
        self.port_field = tk.Entry(self.root)
        self.port_field.insert(0, self.default_port)
        self.port_field.pack()
        
        tk.Label(self.root, text="Number of Packets to Send").pack()
        self.count_field = tk.Entry(self.root)
        self.count_field.insert(0, self.default_count)
        self.count_field.pack()
        
        self.transmit_button = tk.Button(
            self.root, 
            text="Start Transmission", 
            command=self.initiate_transmission
        )
        self.transmit_button.pack()

    def initiate_transmission(self):
        self.transmit_button.config(state="disabled")
        
        try:
            ip = self.ip_field.get()
            port = int(self.port_field.get())
            count = int(self.count_field.get())
            
            if port < 1 or port > 65535:
                raise ValueError("Port must be between 1 and 65535")
                
            if count <= 0:
                raise ValueError("Packet count must be positive")
                
        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve))
            self.transmit_button.config(state="normal")
            return

        transmitter = PacketTransmitter(ip, port, count)
        thread = threading.Thread(
            target=self.execute_transmission, 
            args=(transmitter,),
            daemon=True
        )
        thread.start()

    def execute_transmission(self, transmitter):
        success, message = transmitter.transmit()
        
        self.root.after(0, self.transmission_complete, success, message)

    def transmission_complete(self, success, message):
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Transmission Error", message)
            
        self.transmit_button.config(state="normal")


if __name__ == "__main__":
    NetworkClientGUI()