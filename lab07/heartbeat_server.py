import socket
import time
import threading

HOST = 'localhost'
PORT = 12000
TIMEOUT = 5
CHECK_INTERVAL = 2

clients = {}  # {client_address: last_received_time}

def handle_client(client_address, message):
    current_time = time.time()
    seq_num, send_time = message.split()[1:]
    send_time = float(send_time)
    rtt = current_time - send_time
    print(f"Received heartbeat from {client_address}, seq={seq_num}, RTT={rtt:.3f}s")
    clients[client_address] = current_time

def check_inactive_clients():
    while True:
        current_time = time.time()
        for client_address, last_time in list(clients.items()):
            if current_time - last_time > TIMEOUT:
                print(f"Client {client_address} is inactive")
                del clients[client_address]
        time.sleep(CHECK_INTERVAL)

def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, PORT))
    print(f"Server started on {HOST}:{PORT}")

    threading.Thread(target=check_inactive_clients, daemon=True).start()

    while True:
        message, client_address = server_socket.recvfrom(1024)
        message = message.decode()
        handle_client(client_address, message)

if __name__ == "__main__":
    server()