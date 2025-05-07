import socket
import sys
import threading

IPV6_LOCALHOST = '::1'
ECHO_PORT = 5000
MAX_BUFFER = 1024

class NetworkServer:
    def __init__(self, host=IPV6_LOCALHOST, port=ECHO_PORT, buffer_size=MAX_BUFFER):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.server_socket = None

    def initialize_socket(self):
        self.server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port, 0, 0))
        self.server_socket.listen(5)

    def process_client(self, client_sock, client_addr):
        try:
            while True:
                data = client_sock.recv(self.buffer_size)
                if not data:
                    break
                received_text = data.decode('utf-8')
                print(f"Received from {client_addr}: {received_text}")
                reply_text = received_text.upper()
                client_sock.send(reply_text.encode('utf-8'))
                print(f"Sent to client {client_addr}: {reply_text}")
        except Exception as e:
            print(f"Error handling client {client_addr}: {e}")
        finally:
            client_sock.close()
            print(f"Client {client_addr} disconnected")

    def run(self):
        try:
            self.initialize_socket()
            print(f"Server started on {self.host}:{self.port}")
            while True:
                client_sock, client_addr = self.server_socket.accept()
                print(f"Client connected: {client_addr}")
                client_thread = threading.Thread(target=self.process_client, args=(client_sock, client_addr))
                client_thread.start()
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()

class NetworkClient:
    def __init__(self, host=IPV6_LOCALHOST, port=ECHO_PORT, buffer_size=MAX_BUFFER):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.client_socket = None

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port, 0, 0))
        print(f"Connected to server {self.host}:{self.port}")

    def communicate(self):
        try:
            while True:
                user_input = input("Enter message (or 'exit' to quit): ")
                if user_input.lower() == 'exit':
                    break
                self.client_socket.send(user_input.encode('utf-8'))
                response = self.client_socket.recv(self.buffer_size).decode('utf-8')
                print(f"Server response: {response}")
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            if self.client_socket:
                self.client_socket.close()

    def run(self):
        try:
            self.connect()
            self.communicate()
        except Exception as e:
            print(f"Connection error: {e}")

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ['server', 'client']:
        print("Usage: python ipv6.py [server|client]")
        sys.exit(1)

    if sys.argv[1] == 'server':
        server = NetworkServer()
        server.run()
    else:
        client = NetworkClient()
        client.run()

if __name__ == "__main__":
    main()