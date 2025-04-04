import socket
import sys

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(('', 8080))
    except socket.error as e:
        print(f"Bind error: {e}")
        sys.exit(1)
    print("Client started and listening on port 8080...")
    while True:
        data, addr = sock.recvfrom(1024)
        received_time = data.decode('utf-8')
        print(f"Received time from {addr}: {received_time}")

if __name__ == "__main__":
    main()