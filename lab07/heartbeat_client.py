import socket
import time
import sys

HOST = 'localhost'
PORT = 12000
SEND_INTERVAL = 2 # seconds

def client(client_id):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (HOST, PORT)
    seq_num = 1

    while True:
        send_time = time.time()
        message = f"Heartbeat {seq_num} {send_time}"
        client_socket.sendto(message.encode(), server_address)
        print(f"Sent heartbeat {seq_num} to server (client_id={client_id})")
        seq_num += 1
        time.sleep(SEND_INTERVAL)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python client.py <client_id>")
        sys.exit(1)
    client_id = sys.argv[1]
    client(client_id)