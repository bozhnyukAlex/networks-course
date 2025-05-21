import json
import random

class Router:
    def __init__(self, ip):
        self.ip = ip
        self.neighbors = set()
        self.routing_table = {}
        self.pending_updates = []

    def add_neighbor(self, neighbor_ip):
        self.neighbors.add(neighbor_ip)

    def initialize_table(self):
        self.routing_table[self.ip] = (self.ip, 0)
        for neighbor in self.neighbors:
            self.routing_table[neighbor] = (neighbor, 1)

    def send_updates(self, network):
        for neighbor_ip in self.neighbors:
            if neighbor_ip in network:
                neighbor_router = network[neighbor_ip]
                update = dict(self.routing_table)
                neighbor_router.pending_updates.append((self.ip, update))

    def process_updates(self):
        changed = False
        for source_ip, update_table in self.pending_updates:
            for dest, (nh, metric) in update_table.items():
                new_metric = metric + 1
                if new_metric >= 16:
                    continue
                if dest not in self.routing_table:
                    self.routing_table[dest] = (source_ip, new_metric)
                    changed = True
                else:
                    current_nh, current_metric = self.routing_table[dest]
                    if new_metric < current_metric:
                        self.routing_table[dest] = (source_ip, new_metric)
                        changed = True
        self.pending_updates.clear()
        return changed

def load_network_from_json(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    network = {}
    for ip in data.get('routers', []):
        network[ip] = Router(ip)
    for edge in data.get('edges', []):
        a, b = edge[0], edge[1]
        if a in network and b in network:
            network[a].add_neighbor(b)
            network[b].add_neighbor(a)
    return network

def generate_random_network(num_routers=5):
    network = {}
    ips = []
    used_ips = set()
    for _ in range(num_routers):
        while True:
            ip = ".".join(str(random.randint(0, 255)) for _ in range(4))
            if ip not in used_ips:
                break
        used_ips.add(ip)
        ips.append(ip)
        network[ip] = Router(ip)
    for i in range(num_routers - 1):
        a = ips[i]
        b = ips[i+1]
        network[a].add_neighbor(b)
        network[b].add_neighbor(a)
    additional_edges = num_routers // 2
    added = 0
    while added < additional_edges:
        a, b = random.sample(ips, 2)
        if b not in network[a].neighbors:
            network[a].add_neighbor(b)
            network[b].add_neighbor(a)
            added += 1
    return network

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python rip_emulator.py [json_file | random]")
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
    
    for router in network.values():
        router.initialize_table()
    
    changes = True
    while changes:
        changes = False
        for r in network.values():
            r.pending_updates.clear()
        for r in network.values():
            r.send_updates(network)
        for r in network.values():
            if r.process_updates():
                changes = True
    
    for r in network.values():
        print(f"Final state of router {r.ip} table:")
        print("[Source IP]      [Destination IP]    [Next Hop]       [Metric]  ")
        for dest, (next_hop, metric) in sorted(r.routing_table.items()):
            print(f"{r.ip:<15} {dest:<15} {next_hop:<15} {metric}")

if __name__ == "__main__":
    main()