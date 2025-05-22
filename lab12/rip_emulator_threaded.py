import json
import socket
import threading
import random
import time

class RouterProcess(threading.Thread):
    def __init__(self, name, ip, port, neighbors, network_config):
        super().__init__()
        self.name = name
        self.ip = ip
        self.port = port
        self.neighbors = neighbors
        self.network_config = network_config
        self.routing_table = {}
        self.pending_updates = []
        self.lock = threading.Lock()
        self.running = True
        self.changed = False

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server_socket.bind((self.ip, self.port))
        except Exception as e:
            print(f"[{self.name}] Failed to bind {self.ip}:{self.port}: {e}")
            raise
        self.server_socket.listen(5)
        self.server_thread = threading.Thread(target=self.listen_for_updates, daemon=True)
        self.server_thread.start()

    def initialize_table(self):
        self.routing_table[self.name] = (self.name, 0)
        for neighbor_name, _, _ in self.neighbors:
            self.routing_table[neighbor_name] = (neighbor_name, 1)

    def listen_for_updates(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                data = conn.recv(4096)
                if data:
                    update = json.loads(data.decode())
                    with self.lock:
                        self.pending_updates.append(update)
                conn.close()
            except Exception as e:
                if self.running:
                    pass
                break

    def send_update_to_neighbor(self, neighbor_ip, neighbor_port, table):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect((neighbor_ip, neighbor_port))
                s.sendall(json.dumps(table).encode())
        except Exception as e:
            pass

    def send_updates(self):
        for _, neighbor_ip, neighbor_port in self.neighbors:
            self.send_update_to_neighbor(neighbor_ip, neighbor_port, self.routing_table)

    def process_updates(self):
        self.changed = False
        with self.lock:
            for update in self.pending_updates:
                for dest, (nh, metric) in update.items():
                    new_metric = metric + 1
                    if new_metric >= 16:
                        continue
                    if dest not in self.routing_table:
                        self.routing_table[dest] = (nh, new_metric)
                        self.changed = True
                    else:
                        current_nh, current_metric = self.routing_table[dest]
                        if new_metric < current_metric:
                            self.routing_table[dest] = (nh, new_metric)
                            self.changed = True
            self.pending_updates.clear()
        return self.changed

    def run(self):
        while self.running:
            time.sleep(0.1)

    def stop(self):
        self.running = False
        self.server_socket.close()
        self.server_thread.join(timeout=1)


def generate_random_network(num_routers=5):
    network = {}
    router_names = [f"R{i+1}" for i in range(num_routers)]
    ips = ["127.0.0.1"] * num_routers
    ports = random.sample(range(10000, 60000), num_routers)

    for name, ip, port in zip(router_names, ips, ports):
        network[name] = {
            "name": name,
            "ip": ip,
            "port": port,
            "neighbors": []
        }

    routers = list(network.values())
    for i in range(len(routers) - 1):
        curr = routers[i]
        next_router = routers[i + 1]
        curr["neighbors"].append((next_router["name"], next_router["ip"], next_router["port"]))
        next_router["neighbors"].append((curr["name"], curr["ip"], curr["port"]))

    additional_edges = num_routers // 2
    added = 0
    while added < additional_edges:
        a, b = random.sample(routers, 2)
        pair1 = (b["name"], b["ip"], b["port"])
        pair2 = (a["name"], a["ip"], a["port"])
        found = False
        for n in a["neighbors"]:
            if n[0] == b["name"]:
                found = True
                break
        if not found:
            a["neighbors"].append(pair1)
            b["neighbors"].append(pair2)
            added += 1

    return network


def load_network_from_json(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    network = {}

    routers_data = data.get("routers", [])
    edges = data.get("edges", [])

    name_to_ip_port = {}
    for name in routers_data:
        name_to_ip_port[name] = ("127.0.0.1", random.randint(10000, 60000))

    for name in routers_data:
        ip, port = name_to_ip_port[name]
        network[name] = {
            "name": name,
            "ip": ip,
            "port": port,
            "neighbors": []
        }

    for a, b in edges:
        if a in network and b in network:
            a_ip, a_port = name_to_ip_port[a]
            b_ip, b_port = name_to_ip_port[b]
            network[a]["neighbors"].append((b, b_ip, b_port))
            network[b]["neighbors"].append((a, a_ip, a_port))

    return network


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python rip_emulator_threaded.py [json_file | random]")
        return

    option = sys.argv[1]
    if option.endswith('.json'):
        try:
            network = load_network_from_json(option)
        except Exception as e:
            print(f"Error loading JSON: {e}")
            return
    else:
        network = generate_random_network()

    if not network:
        print("Network is empty.")
        return

    routers = {}
    for name, info in network.items():
        router = RouterProcess(name, info["ip"], info["port"], info["neighbors"], network)
        router.initialize_table()
        router.start()
        routers[name] = router

    step = 0
    all_changed = True

    try:
        while all_changed:
            all_changed = False
            step += 1

            print(f"\n{'-' * 60}")
            print(f"Simulation step {step}")
            print(f"{'-' * 60}")

            threads = []
            for router in routers.values():
                t = threading.Thread(target=router.send_updates)
                threads.append(t)
                t.start()
            for t in threads:
                t.join()

            time.sleep(0.5)

            changed_in_step = False
            for router in routers.values():
                if router.process_updates():
                    changed_in_step = True
            all_changed = changed_in_step

            for name, router in routers.items():
                print(f"Simulation step {step} of router {name}")
                print("[Source IP]      [Destination IP]    [Next Hop]       [Metric]  ")
                for dest, (nh, metric) in sorted(router.routing_table.items()):
                    print(f"{name:<15} {dest:<15} {nh:<15} {metric}")
                print()
    except KeyboardInterrupt:
        print("Stopping simulation...")
    finally:
        for r in routers.values():
            r.stop()
        for r in routers.values():
            r.join(timeout=1)


if __name__ == "__main__":
    main()