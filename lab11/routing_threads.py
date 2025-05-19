import threading
import queue
import time

update_lock = threading.Lock()
update_counter = 0

class Node(threading.Thread):
    def __init__(self, node_id, adjacent_nodes, initial_costs, stop_event):
        threading.Thread.__init__(self)
        self.node_id = node_id
        self.adjacent_nodes = adjacent_nodes
        self.routes = {node_id: (0, node_id)}
        for neighbor_id, cost in initial_costs.items():
            self.routes[neighbor_id] = (cost, neighbor_id)
        self.queue = queue.Queue()
        self.stop_event = stop_event

    def get_routing_vector(self):
        return {dest: cost for dest, (cost, _) in self.routes.items()}

    def send_vector_to_neighbors(self):
        vector = self.get_routing_vector()
        for neighbor in self.adjacent_nodes:
            neighbor.queue.put(("vector", self.node_id, vector))

    def process_vector(self, sender_id, vector):
        updated = False
        sender_cost = self.routes[sender_id][0]
        for dest, cost in vector.items():
            total_cost = cost + sender_cost
            if dest not in self.routes or total_cost < self.routes[dest][0]:
                self.routes[dest] = (total_cost, sender_id)
                updated = True
        return updated

    def update_cost(self, neighbor_id, new_cost):
        if neighbor_id in self.routes:
            old_cost = self.routes[neighbor_id][0]
            self.routes[neighbor_id] = (new_cost, neighbor_id)
            return old_cost != new_cost
        return False

    def run(self):
        global update_counter
        self.send_vector_to_neighbors()
        while not self.stop_event.is_set():
            try:
                message = self.queue.get(timeout=0.1)
                msg_type, *data = message
                if msg_type == "vector":
                    sender_id, vector = data
                    if self.process_vector(sender_id, vector):
                        self.send_vector_to_neighbors()
                        with update_lock:
                            update_counter += 1
                elif msg_type == "cost_update":
                    neighbor_id, new_cost = data
                    if self.update_cost(neighbor_id, new_cost):
                        self.send_vector_to_neighbors()
                        with update_lock:
                            update_counter += 1
            except queue.Empty:
                continue

def display_routes(nodes):
    for node in nodes.values():
        print(f"\nRouting table for node {node.node_id}:")
        for dest, (cost, next_hop) in node.routes.items():
            print(f"  To {dest}: cost {cost}, next hop {next_hop}")

def update_link_cost(nodes, node1_id, node2_id, new_cost):
    nodes[node1_id].queue.put(("cost_update", node2_id, new_cost))
    nodes[node2_id].queue.put(("cost_update", node1_id, new_cost))

neighbors = {
    0: [1, 3],
    1: [0, 2, 3],
    2: [1, 3],
    3: [0, 1, 2]
}

initial_costs = {
    0: {1: 1, 3: 7},
    1: {0: 1, 2: 1, 3: 3},
    2: {1: 1, 3: 2},
    3: {0: 7, 1: 3, 2: 2}
}

stop_event = threading.Event()
nodes = {}
for node_id in neighbors:
    nodes[node_id] = Node(node_id, [], initial_costs[node_id], stop_event)
for node in nodes.values():
    node.adjacent_nodes = [nodes[adj_id] for adj_id in neighbors[node.node_id]]

for node in nodes.values():
    node.start()

def monitor_convergence():
    stability_count = 0
    previous_counter = 0
    while True:
        time.sleep(1)
        with update_lock:
            current_counter = update_counter
        if current_counter == previous_counter:
            stability_count += 1
            if stability_count >= 3:
                break
        else:
            stability_count = 0
        previous_counter = current_counter
    return previous_counter

print("Starting initial vector exchange...")
monitor_convergence()
print("Initial convergence achieved")
display_routes(nodes)

print("\nChanging cost between nodes 0 and 3 from 7 to 8...")
update_link_cost(nodes, 0, 3, 8)

print("\nStarting vector exchange after cost change...")
monitor_convergence()
print("Convergence achieved after cost update")
display_routes(nodes)

stop_event.set()
for node in nodes.values():
    node.join()