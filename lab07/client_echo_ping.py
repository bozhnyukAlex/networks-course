import socket
import time
import statistics

def client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(1.0)
    server_address = ('localhost', 12000)
    
    num_packets = 10
    rtt_list = []
    lost_packets = 0
    
    for sequence_number in range(1, num_packets + 1):
        send_time = time.time()
        message = f"Ping {sequence_number} {send_time}"
        try:
            client_socket.sendto(message.encode(), server_address)
            response, _ = client_socket.recvfrom(1024)
            receive_time = time.time()
            rtt = receive_time - send_time
            rtt_list.append(rtt)
            print(f"Reply from {server_address[0]}: bytes={len(response)} time={rtt:.3f}s")        
        except socket.timeout:
            lost_packets += 1
            print("Request timed out")
    client_socket.close()
    
    total_packets = num_packets
    received_packets = total_packets - lost_packets
    loss_percentage = (lost_packets / total_packets) * 100 if total_packets > 0 else 0
    print(f"\n--- {server_address[0]} ping statistics ---")
    print(f"{total_packets} packets transmitted, {received_packets} received, "
          f"{loss_percentage:.0f}% packet loss")
    
    if rtt_list:
        min_rtt = min(rtt_list)
        max_rtt = max(rtt_list)
        avg_rtt = statistics.mean(rtt_list)
        print(f"rtt min/avg/max = {min_rtt:.3f}/{avg_rtt:.3f}/{max_rtt:.3f} s")
    else:
        print("No RTT statistics available (all packets lost).")
        
if __name__ == "__main__":
    client()