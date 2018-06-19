from random import *
from copy import *
from Block import *
from BlockDAG import *
from Node import *

def get_poisson_plus_one(lam):
    result = 1
    t = (-1.0/lam)*log(random())
    while t < 1.0:
        result += 1
        t += (-1.0/lam)*log(random())
    return result

class Graph(object):
    def __init__(self, inp):
        # inp = {"initial population": 25, "number of outgoing connections": 3, "simulation runtime": 10000.0
        #        "birth rate": 1.0, "death rate": 1.0, "average edge length": 30.0, "edge length dist": "poisson",
        #        "parent selection": "Bitcoin", "difficulty update period": 5,
        #        "target median inter-arrival wait time": 60.0, "depth": 3, "clockshift": 0.0, "hashrate": 1.0})
        self.nodes = {}
        self.clock = 0.0
        self.params = deepcopy(inp)
        self.genesis = None
        self.genesis = self._initialize()

    def _initialize(self):
        block_dag_params = {"difficulty update period": self.params["difficulty update period"]}
        block_dag_params.update({"target median inter-arrival wait time": self.params["target median inter-arrival wait time"]})
        block_dag_params.update({"depth": self.params["depth"], "parent selection": self.params["parent selection"]})
        node_params = {"clockshift": self.params["clockshift"], "hashrate": self.params["hashrate"]}
        node_params.update({"blockdag parameters": block_dag_params})

        for i in range(self.params["initial population"]):
            x = Node(inp=node_params)
            self.nodes.update({x.node_id: x})

        k = self.params["number of outgoing connections"]
        for node_id in self.nodes:
            this_node = self.nodes[node_id]

            # Pick neighbors
            neighbors = []
            popln = list(self.nodes.keys())
            while len(neighbors) < k:
                candidate = choice(popln)
                while candidate in neighbors or candidate == node_id:
                    candidate = choice(popln)
                neighbors.append(candidate)

            # Add an edge for each neighbor
            for neighbor_id in neighbors:
                that_node = self.nodes[neighbor_id]
                if self.params["edge length dist"] == "poisson":
                    lam = float(self.params["average edge length"]-1)
                    length = get_poisson_plus_one(lam)
                else:
                    length = random()
                assert length > 0.0
                edge_params = {"source": this_node, "target": that_node, "length": length}
                ed = Edge(edge_params)
                this_node.edges.update({ed.edge_id: ed})
                assert ed.source.node_id in self.nodes
                assert ed.target.node_id in self.nodes
                assert len(ed.incoming)==0
                assert type(ed.incoming)==type([])

        # To avoid problems, we pick a random node to start the process.
        #genesis_params = {"block ID": None, "timestamp": self.clock, "parents": None, "difficulty": 1.0}
        #rand_node_id = choice(list(self.nodes.keys()))
        #rand_node = self.nodes[rand_node_id]
        #b = rand_node.find_block(genesis_params, relay=True)
        #genesis_params["block ID"] = b.block_id
        #genesis_params["timestamp"] = b.timestamp
        #genesis_params["parents"] = None
        #for node_id in self.nodes:
        #    this_node = self.nodes[node_id]
        #    this_node.find_block(genesis_params, relay=False)

        #return genesis_params

    def check(self):
        for node_id in self.nodes:
            node = self.nodes[node_id]
            for edge_id in node.edges:
                ed = node.edges[edge_id]
                if len(ed.incoming) > 0:
                    for entry in ed.incoming:
                        assert entry[0] > 0.0

    def describe(self):
        self.check()
        line = ""
        for node_id in self.nodes:
            node = self.nodes[node_id]
            line += "Node with ID"
            line += ", " + str(node_id)
            line += ", is connected to the following node IDs"
            for edge_id in node.edges:
                ed = node.edges[edge_id]
                line += ", " + str(ed.target.node_id)
            line += ", with respective edge IDs"
            for edge_id in node.edges:
                line += ", " + str(edge_id)
            line += "\n"
        self.check()
        return line

    def birth_node(self):
        self.check()
        k = self.params["number of outgoing connections"]
        block_dag_params = {"difficulty update period": 5, "target median inter-arrival wait time": 60.0, "depth": 3,
                            "parent selection": "Bitcoin"}
        node_params = {"node ID": None, "clockshift": 0.0, "hashrate": 1.0, "edge dict": {},
                       "blockdag parameters": block_dag_params}
        this_node = Node(inp=node_params)
        self.nodes.update({this_node.node_id: this_node})

        neighbors = []
        if len(self.nodes) < k:
            neighbors = [self.nodes[node_id] for node_id in self.nodes]
        else:
            while len(neighbors) < k and len(self.nodes) > 2:
                candidate = choice(list(self.nodes.keys()))
                while candidate in neighbors:
                    candidate = choice(list(self.nodes.keys()))
                neighbors.append(self.nodes[candidate])

        for that_node in neighbors:
            edge_params = {"edge ID": None, "source": this_node, "target": that_node, "length": None}
            ed = Edge(edge_params)
            this_node.edges.update({ed.edge_id: ed})

        # Sync new node by copying a random neighbor
        neighbor_to_copy = choice(neighbors)
        this_node.block_dag = deepcopy(neighbor_to_copy.block_dag)

        # Report result
        output = ""
        output += "Node with ID " + str(this_node.node_id) + " joined the network and connected to nodes"
        for edge_id in this_node.edges:
            ed = this_node.edges[edge_id]
            neighbor = ed.target
            output += ", " + str(neighbor.node_id)
        output += ", and with respective edge IDs"
        for edge_id in this_node.edges:
            output += ", " + str(edge_id)
        output += ", and bootstraps the blockdag by copying neighbor with node ID, "
        output += str(neighbor_to_copy.node_id)
        self.check()
        return output

    def kill_node(self):
        self.check()
        output = ""
        if len(self.nodes) <= 1:
            # Record result
            output += "Kill node = network extinction. No action taken."
        elif len(self.nodes) > 1:
            node_id_to_kill = choice(list(self.nodes.keys()))
            node_to_kill = self.nodes[node_id_to_kill]

            record = []

            for node_id in self.nodes:
                this_node = self.nodes[node_id]
                for edge_id in this_node.edges:
                    ed = this_node.edges[edge_id]
                    if ed.target == node_to_kill:
                        new_neighbor_id = choice(list(self.nodes.keys()))
                        while new_neighbor_id == node_id_to_kill or new_neighbor_id == this_node.node_id:
                            new_neighbor_id = choice(list(self.nodes.keys()))
                        new_neighbor = self.nodes[new_neighbor_id]
                        ed.target = new_neighbor
                        record.append((edge_id, new_neighbor.node_id))
                        ed.incoming = []
            del self.nodes[node_id_to_kill]

            # Record result
            output += "Node with ID " + str(node_id_to_kill) + " left the network. For each of the following (edge_id, node_id), edge with ID edge_id has new target node with ID node_id"
            for entry in record:
                (eid, nid) = entry
                output += ", (" + str(nid) + ", " + str(eid) + ")"
        self.check()
        return output


    def new_block(self, event_data):
        self.check()
        # event_data is just some node_id
        node_id_of_finder = event_data
        assert node_id_of_finder in self.nodes
        node = self.nodes[node_id_of_finder]
        assert self.clock > 0.0
        ts = self.clock
        assert ts > 0.0
        b = node.find_block({"timestamp": ts}, relay=True)
        self.check()

        # Record result
        output = ""
        output += "Node with ID, " + str(node_id_of_finder) + ", found a new block with block ID, "
        output += str(b.block_id) + ", and timestamp "
        if b.parents is not None:
            parent_list = str(b.parents)
        else:
            parent_list = "None"
        output += str(b.timestamp) + ", and parents, " + parent_list
        self.check()
        return output

    def push_blocks(self):
        output = ""
        for node_id in self.nodes:
            node = self.nodes[node_id]
            for edge_id in node.edges:
                ed = node.edges[edge_id]
                output += str(ed.push_all())
        self.check()
        return output

    def roll_time(self, delta_t):
        self.post_roll_time_check()
        self.clock += delta_t
        for node_id in self.nodes:
            node = self.nodes[node_id]
            for edge_id in node.edges:
                ed = node.edges[edge_id]
                if len(ed.incoming) > 0:
                    for entry in ed.incoming:
                        entry[0] -= delta_t
        self.post_roll_time_check()

    def post_roll_time_check(self):
        for node_id in self.nodes:
            node = self.nodes[node_id]
            for edge_id in node.edges:
                ed = node.edges[edge_id]
                if len(ed.incoming) > 0:
                    for entry in ed.incoming:
                        assert entry[0] >= 0.0


class TestGraph(unittest.TestCase):
    def test_graph(self):
        # Test _initialize
        # Test describe
        # Test birth_node
        # Test kill_node
        # Test new_block
        # Test push_block
        # Test roll_time
        pass


suite = unittest.TestLoader().loadTestsFromTestCase(TestGraph)
unittest.TextTestRunner(verbosity=1).run(suite)
