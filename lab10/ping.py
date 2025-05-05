import socket
import struct
import time
import select
import statistics

ICMP_ECHO_REQUEST = 8
ICMP_CODE = 0
TIMEOUT = 1  # seconds

ICMP_ERRORS = {
    (3, 0): "Destination Network Unreachable",
    (3, 1): "Destination Host Unreachable",
    (3, 2): "Destination Protocol Unreachable",
    (3, 3): "Destination Port Unreachable",
    (3, 4): "Fragmentation Needed and DF Set",
    (3, 5): "Source Route Failed",
    (11, 0): "Time to Live Exceeded in Transit",
    (11, 1): "Fragment Reassembly Time Exceeded",
}

def checksum(source_string):
    """
    Calculates the checksum for the ICMP packet.
    """
    sum = 0
    count_to = (len(source_string) // 2) * 2
    count = 0
    while count < count_to:
        this_val = source_string[count + 1] * 256 + source_string[count]
        sum = sum + this_val
        sum = sum & 0xffffffff
        count = count + 2
    if count_to < len(source_string):
        sum = sum + source_string[len(source_string) - 1]
        sum = sum & 0xffffffff
    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def create_packet(id, sequence):
    """
    Creates an ICMP echo request packet.
    """
    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, ICMP_CODE, 0, id, sequence)
    data = struct.pack('d', time.time())
    my_checksum = checksum(header + data)
    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, ICMP_CODE, socket.htons(my_checksum), id, sequence)
    return header + data

def ping(host, count=4):
    """
    Sends ICMP echo requests to the host and displays statistics with error handling.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except socket.error as e:
        print(f"Socket creation error: {e}")
        return

    try:
        dest_addr = socket.gethostbyname(host)
    except socket.gaierror as e:
        print(f"Address resolution error: {e}")
        return

    print(f"PING {host} ({dest_addr})")

    rtts = []
    lost = 0

    for i in range(count):
        packet = create_packet(id=1, sequence=i)
        sock.sendto(packet, (dest_addr, 0))
        send_time = time.time()

        while True:
            ready = select.select([sock], [], [], TIMEOUT)
            if ready[0] == []:  # Timeout
                lost += 1
                print(f"Request timed out.")
                break
            else:
                recv_packet, addr = sock.recvfrom(1024)
                recv_time = time.time()
                icmp_type, icmp_code, _, _, _ = struct.unpack('bbHHh', recv_packet[20:28])

                if icmp_type == 0:  # Echo reply
                    send_timestamp = struct.unpack('d', recv_packet[28:])[0]
                    rtt = (recv_time - send_timestamp) * 1000  # in milliseconds
                    rtts.append(rtt)
                    print(f"Reply from {addr[0]}: time={rtt:.2f}ms")
                    break
                elif (icmp_type, icmp_code) in ICMP_ERRORS:
                    error_msg = ICMP_ERRORS.get((icmp_type, icmp_code), "Unknown error")
                    print(f"Error from {addr[0]}: {error_msg}")
                    lost += 1
                    break
                else:
                    print(f"Unexpected ICMP type {icmp_type} code {icmp_code}")
                    lost += 1
                    break

        time.sleep(1)

    if rtts:
        print(f"\nPing statistics for {host}:")
        print(f"    Packets: sent = {count}, received = {count - lost}, lost = {lost} ({lost / count * 100:.0f}% loss),")
        print(f"    Approximate round-trip times in milliseconds:")
        print(f"    Minimum = {min(rtts):.2f}ms, Maximum = {max(rtts):.2f}ms, Average = {statistics.mean(rtts):.2f}ms")
    else:
        print("All packets lost or errors received.")

    sock.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ping.py <host>")
    else:
        ping(sys.argv[1])