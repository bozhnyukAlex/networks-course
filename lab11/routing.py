class Node:
    def __init__(self, id, adjacent_nodes, initial_costs):
        self.id = id
        self.adjacent_nodes = adjacent_nodes
        self.routes = {id: (0, id)}
        for neighbor_id, cost in initial_costs.items():
            self.routes[neighbor_id] = (cost, neighbor_id)

    def get_routing_vector(self):
        return {dest: cost for dest, (cost, _) in self.routes.items()}

    def update_routes(self, sender_id, vector, sender_cost):
        updated = False
        for dest, cost in vector.items():
            if cost == float('inf'):
                continue
            total_cost = cost + sender_cost
            if dest not in self.routes or self.routes[dest][0] > total_cost:
                self.routes[dest] = (total_cost, sender_id)
                updated = True
        return updated

    def set_neighbor_cost(self, neighbor_id, new_cost):
        if neighbor_id in self.routes:
            old_cost = self.routes[neighbor_id][0]
            self.routes[neighbor_id] = (new_cost, neighbor_id)
            return old_cost != new_cost
        return False

class Network:
    def __init__(self, neighbors, initial_costs):
        self.nodes = {}
        for node_id in neighbors:
            self.nodes[node_id] = Node(node_id, [], initial_costs[node_id])
        for node in self.nodes.values():
            node.adjacent_nodes = [self.nodes[adj_id] for adj_id in neighbors[node.id]]

    def simulate_routing(self, max_iterations=10):
        iteration = 0
        while True:
            updated = False
            for node in self.nodes.values():
                vector = node.get_routing_vector()
                for neighbor in node.adjacent_nodes:
                    sender_cost = node.routes[neighbor.id][0]
                    if neighbor.update_routes(node.id, vector, sender_cost):
                        updated = True
            iteration += 1
            if not updated:
                print(f"Routing tables stabilized at iteration {iteration}")
                break
            if iteration >= max_iterations:
                print("Maximum number of iterations reached")
                break

    def display_routes(self):
        for node in self.nodes.values():
            print(f"\nRouting table for node {node.id}:")
            for dest, (cost, next_hop) in node.routes.items():
                print(f"  To {dest}: cost {cost}, next hop {next_hop}")

    def update_link_cost(self, node1_id, node2_id, new_cost):
        self.nodes[node1_id].set_neighbor_cost(node2_id, new_cost)
        self.nodes[node2_id].set_neighbor_cost(node1_id, new_cost)

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

network = Network(neighbors, initial_costs)

print("Starting initial vector exchange...")
network.simulate_routing()
print("\nInitial routing tables:")
network.display_routes()

print("\nChanging the cost between nodes 0 and 3 from 7 to 8...")
network.update_link_cost(0, 3, 8)

print("\nStarting vector exchange after cost change...")
network.simulate_routing()
print("\nRouting tables after cost change:")
network.display_routes()