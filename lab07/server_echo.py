import random
import socket

def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('localhost', 12000))
    
    print("Server is running")
    
    while True:
        message, client_address = server_socket.recvfrom(1024)
        if random.random() < 0.2:
            continue
        
        modified_message = message.decode().upper()
        server_socket.sendto(modified_message.encode(), client_address)

if __name__ == "__main__":
    server()