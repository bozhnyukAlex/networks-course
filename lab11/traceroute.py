import socket
import struct
import time
import sys

ICMP_ECHO_REQUEST = 8
ICMP_TIME_EXCEEDED = 11
ICMP_ECHO_REPLY = 0

MAX_HOPS = 30

TIMEOUT = 2.0

def compute_checksum(payload):
    total = 0
    for i in range(0, len(payload) - 1, 2):
        total += (payload[i] << 8) + payload[i + 1]
    if len(payload) % 2:
        total += payload[-1] << 8
    total = (total >> 16) + (total & 0xffff)
    total += (total >> 16)
    return ~total & 0xffff

def generate_icmp_packet():
    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, 0, 1, 1)
    data = b''
    packet_checksum = compute_checksum(header + data)
    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, socket.htons(packet_checksum), 1, 1)
    return header + data

def lookup_hostname(ip_address):
    try:
        return socket.gethostbyaddr(ip_address)[0]
    except socket.herror:
        return None

def perform_traceroute(destination, max_ttl=MAX_HOPS, messages_per_hop=3, response_timeout=TIMEOUT):
    try:
        destination_ip = socket.gethostbyname(destination)
    except socket.gaierror:
        print(f"Failed to resolve address {destination}")
        return
    print(f"Tracing route to {destination} [{destination_ip}] with maximum hops {max_ttl} and {messages_per_hop} messages per hop:")
    for ttl in range(1, max_ttl + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as raw_socket:
            raw_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
            raw_socket.settimeout(response_timeout)
            ping_times = []
            intermediate_ip = None
            target_reached = False
            for _ in range(messages_per_hop):
                packet = generate_icmp_packet()
                send_time = time.time()
                raw_socket.sendto(packet, (destination_ip, 0))
                try:
                    received_data, source_addr = raw_socket.recvfrom(1024)
                    receive_time = time.time()
                    ping_time = (receive_time - send_time) * 1000
                    ping_times.append(ping_time)
                    message_type, = struct.unpack('b', received_data[20:21])
                    intermediate_ip = source_addr[0]
                    if message_type == ICMP_ECHO_REPLY:
                        target_reached = True
                        break
                    elif message_type == ICMP_TIME_EXCEEDED:
                        break
                except socket.timeout:
                    ping_times.append(None)
            if all(pt is None for pt in ping_times):
                print(f"{ttl:<3}  * " * messages_per_hop)
                continue
            hostname = lookup_hostname(intermediate_ip) if intermediate_ip else None
            time_string = '  '.join(f'{pt:.3f} ms' if pt is not None else '*' for pt in ping_times)
            if hostname:
                print(f"{ttl:<3}  {intermediate_ip} ({hostname})  {time_string}")
            else:
                print(f"{ttl:<3}  {intermediate_ip or '*'}  {time_string}")
            if target_reached:
                break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python traceroute.py <host> [messages_per_hop]")
        sys.exit(1)
    messages_per_hop = 3
    if len(sys.argv) > 2:
        try:
            messages_per_hop = int(sys.argv[2])
            if messages_per_hop <= 0:
                raise ValueError("Messages per hop must be positive")
        except ValueError as e:
            print(f"Invalid messages_per_hop value: {e}")
            sys.exit(1)
    perform_traceroute(sys.argv[1], messages_per_hop=messages_per_hop)