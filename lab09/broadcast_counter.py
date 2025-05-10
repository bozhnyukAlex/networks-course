import socket
import threading
import time
import select
import queue
import tkinter as tk
from tkinter import ttk

class NetworkInstanceMonitor:
    PORT = 5000
    BROADCAST_INTERVAL = 2.0
    INSTANCE_TIMEOUT = 3 * BROADCAST_INTERVAL

    def __init__(self):
        self.message_queue = queue.Queue()
        self.terminate_flag = threading.Event()
        self.peer_list = {}
        self.host_ip = self._fetch_host_ip()
        self.broadcast_sock = None
        self.direct_sock = None
        self.direct_port = None

    def _fetch_host_ip(self):
        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            temp_sock.connect(('255.255.255.255', self.PORT))
            ip_address = temp_sock.getsockname()[0]
        except Exception:
            ip_address = '127.0.0.1'
        finally:
            temp_sock.close()
        return ip_address

    def _initialize_sockets(self):
        self.broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.broadcast_sock.bind(('', self.PORT))

        self.direct_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.direct_sock.bind(('', 0))
        self.direct_port = self.direct_sock.getsockname()[1]
        self.direct_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def _send_packet(self, text, destination):
        self.direct_sock.sendto(text.encode('utf-8'), destination)

    def _handle_packet(self, text, source, timestamp):
        if text == "INIT":
            self._send_packet("ACTIVE", source)
            self.peer_list[source] = timestamp
        elif text == "PING":
            self.peer_list[source] = timestamp
        elif text == "ACTIVE":
            self.peer_list[source] = timestamp
        elif text == "TERMINATE":
            self.peer_list.pop(source, None)

    def _track_peers(self):
        self._initialize_sockets()
        my_location = (self.host_ip, self.direct_port)
        next_broadcast = time.time() + self.BROADCAST_INTERVAL
        next_cleanup = time.time() + 1.0

        self._send_packet("INIT", ('<broadcast>', self.PORT))
        while not self.terminate_flag.is_set():
            ready_socks, _, _ = select.select([self.broadcast_sock, self.direct_sock], [], [], 0.1)
            now = time.time()
            for sock in ready_socks:
                packet, (peer_ip, peer_port) = sock.recvfrom(1024)
                content = packet.decode('utf-8')
                peer = (peer_ip, peer_port)
                if sock == self.broadcast_sock and content in ["INIT", "PING"]:
                    self._handle_packet(content, peer, now)
                elif sock == self.direct_sock and content in ["ACTIVE", "TERMINATE"]:
                    self._handle_packet(content, peer, now)
            if now >= next_broadcast:
                self._send_packet("PING", ('<broadcast>', self.PORT))
                next_broadcast = now + self.BROADCAST_INTERVAL
            if now >= next_cleanup:
                expired = [addr for addr, last in self.peer_list.items() if now - last > self.INSTANCE_TIMEOUT]
                for addr in expired:
                    self.peer_list.pop(addr, None)
                next_cleanup = now + 1.0
            if self.peer_list:
                self.message_queue.put(list(self.peer_list.keys()))
        for peer in self.peer_list:
            if peer != my_location:
                self._send_packet("TERMINATE", peer)
        self.broadcast_sock.close()
        self.direct_sock.close()

    def _update_display(self, window, total_label, peer_box):
        try:
            while not self.message_queue.empty():
                peers = self.message_queue.get_nowait()
                peer_box.delete(0, tk.END)
                for ip, port in sorted(peers):
                    peer_box.insert(tk.END, f"{ip}:{port}")
                total_label.config(text=str(len(peers)))
        except queue.Empty:
            pass
        window.after(100, self._update_display, window, total_label, peer_box)

    def _shutdown(self, window, tracker_thread):
        self.terminate_flag.set()
        tracker_thread.join()
        window.destroy()

    def start(self):
        app_window = tk.Tk()
        app_window.title("Список активных копий")
        app_window.geometry("300x400")
        tk.Label(app_window, text="Активных копий:").pack(pady=5)
        total_label = tk.Label(app_window, text="0")
        total_label.pack()
        tk.Label(app_window, text="Интервал, мс:").pack(pady=5)
        tk.Label(app_window, text="2000").pack()
        peer_box = tk.Listbox(app_window, font="Courier", height=15)
        peer_box.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        exit_btn = ttk.Button(app_window, text="Выход", command=lambda: self._shutdown(app_window, tracker_thread))
        exit_btn.pack(pady=10)
        app_window.protocol("WM_DELETE_WINDOW", lambda: self._shutdown(app_window, tracker_thread))

        tracker_thread = threading.Thread(target=self._track_peers)
        tracker_thread.start()

        app_window.after(100, self._update_display, app_window, total_label, peer_box)
        app_window.mainloop()

if __name__ == "__main__":
    monitor = NetworkInstanceMonitor()
    monitor.start()