import socket
import argparse

def scan_open_ports(host_ip, begin_port, finish_port):
    for num in range(begin_port, finish_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
            connection.settimeout(1)
            try:
                connection.bind((host_ip, num))
                yield num
            except socket.error:
                pass

def main():
    parser = argparse.ArgumentParser(description="Find open ports on a specified IP")
    parser.add_argument("host_ip", help="IP address to examine")
    parser.add_argument("begin_port", type=int, help="Initial port number")
    parser.add_argument("finish_port", type=int, help="Final port number")
    args = parser.parse_args()

    if not (0 <= args.begin_port <= 65535 and 0 <= args.finish_port <= 65535):
        parser.error("Port numbers must be between 0 and 65535")
    if args.begin_port > args.finish_port:
        parser.error("Initial port must not exceed final port")
    try:
        socket.inet_aton(args.host_ip)
    except socket.error:
        parser.error("Incorrect IP address format")

    print(f"Examining ports on {args.host_ip} from {args.begin_port} to {args.finish_port}...")
    open_count = 0
    for port in scan_open_ports(args.host_ip, args.begin_port, args.finish_port):
        print(f"Port {port} is open")
        open_count += 1
    if open_count == 0:
        print("No open ports detected in the range")
    else:
        print(f"Detected {open_count} open ports")

if __name__ == "__main__":
    main()