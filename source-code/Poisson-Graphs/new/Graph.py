from random import *
from copy import *
from Block import *
from BlockDAG import *
from Node import *


class Graph(object):
    def __init__(self, inp):
        self.nodes = {}
        self.clock = 0.0
        self.params = deepcopy(inp)
        self.genesis = None
        self.genesis = self._initialize()

    def _initialize(self):
        for i in range(self.params["initial population"]):
            block_dag_params = {"difficulty update period":5, "target median inter-arrival wait time": 60.0, "depth": 3}
            node_params = {"node ID": None, "clockshift": 0.0, "hashrate": 1.0, "edge dict":{}, "blockdag parameters": block_dag_params}
            x = Node(inp=node_params)
            self.nodes.update({x.node_id: x})

        k = self.params["number of outgoing connections"]
        for node_id in self.nodes:
            this_node = self.nodes[node_id]
            neighbors = []
            popln = list(self.nodes.keys())
            while len(neighbors) < k:
                candidate = choice(popln)
                while candidate in neighbors:
                    candidate = choice(popln)
                neighbors.append(candidate)

            for neighbor_id in neighbors:
                that_node = self.nodes[neighbor_id]
                edge_params = {"edge ID": None, "source": this_node, "target": that_node, "length": None}
                ed = Edge(edge_params)
                this_node.edges.update({ed.edge_id: ed})

        # To avoid problems, we ensure everyone has the same genesis block at self.clock = 0.0
        genesis_params = {"block ID": None, "timestamp": self.clock, "parents": None}
        rand_node_id = choice(list(self.nodes.keys()))
        rand_node = self.nodes[rand_node_id]
        b = rand_node.find_block(genesis_params, relay=False)
        genesis_params["block ID"] = b.block_id
        genesis_params["timestamp"] = b.timestamp
        genesis_params["parents"] = None
        for node_id in self.nodes:
            this_node = self.nodes[node_id]
            this_node.find_block(genesis_params, relay=False)

        return genesis_params

    def describe(self):
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
        return line

    def run(self):
        #print("Beginning run")
        with open("transcript.csv", "w") as transcript:
            line = " #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####\n"
            #print(line)
            transcript.write(line)
            line = "Beginning simulation with simulation parameters {}\n"
            #print(line)
            transcript.write(line)
            line = " #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####\n"
            #print(line)
            transcript.write(line)
            line = "Describing initial state of network."
            #print(line)
            transcript.write(line)
            line = self.describe()
            #print(line)
            transcript.write(line)
            line = " #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####\n"
            #print(line)
            transcript.write(line)
            line = "All blocks are starting with genesis block with ID, " + str(self.genesis["block ID"]) + "\n"
            #print(line)
            transcript.write(line)
            line = " #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####\n"
            #print(line)
            transcript.write(line)
            line = "Describing evolution of the network.\n"
            #print(line)
            transcript.write(line)
            line = "dt,t,eventDescription\n"
            #print(line)
            transcript.write(line)
            while self.clock < self.params["simulation runtime"] and len(self.nodes) > 0:
                line = ""

                dt = (-1.0 / self.params["birth rate"]) * log(random())
                event = "birth"
                #print("Possible birth")

                ds = (-1.0 / self.params["death rate"]) * log(random())
                if ds < dt:
                    dt = ds
                    event = "death"
                    #print("Possible death")

                for node_id in self.nodes:
                    this_node = self.nodes[node_id]
                    ds = this_node.get_time()
                    if ds < dt:
                        dt = ds
                        event = "new," + str(deepcopy(node_id))

                    for edge_id in this_node.edges:
                        ed = this_node.edges[edge_id]
                        if len(ed.incoming) > 0:
                            ed.incoming = sorted(ed.incoming, key=lambda x:x[0])
                            entry = ed.incoming[0]
                            ds = entry[0]
                            if ds < dt:
                                dt = ds
                                event = "push," + str(deepcopy(node_id)) + "," + str(deepcopy(edge_id))

                #print("Rolling the clock forward, modifying wait time of all blocks on all edges")
                line += str(dt) + ","
                self.clock += dt
                for node_id in self.nodes:
                    node = self.nodes[node_id]
                    for edge_id in node.edges:
                        ed = node.edges[edge_id]
                        for [t,b] in ed.incoming:
                            t = t - dt
                line += str(self.clock) + ","

                if event == "birth":
                    #print("Final event for this timestamp was a birth!")
                    line += self.birth_node(event)
                elif event == "death":
                    #print("Final event for this timestamp was a death!")
                    line += self.kill_node(event)
                elif event[:4] == "new,":
                    #print("Final event for this timestamp was discovery of a new block!")
                    line += self.new_block(event)
                elif event[:5] == "push,":
                    #print("Final event for this timestamp was a block push from an edge!")
                    line += self.push_block(event)
                else:
                    line += "Bad output."

                line += "\n"
                transcript.write(line)
                #print(line)
            line = "Simulation terminated\n"
            transcript.write(line)

        return True

    def birth_node(self, event=None):
        #print("Beginning node birth routine")
        output = ""
        if event is not None:
            block_dag_params = {"difficulty update period": 5, "target median inter-arrival wait time": 60.0, "depth": 3}
            node_params = {"node ID": None, "clockshift": 0.0, "hashrate": 1.0, "edge dict": {}, "blockdag parameters": block_dag_params}
            this_node = Node(inp=node_params)
            self.nodes.update({this_node.node_id: this_node})

            k = self.params["number of outgoing connections"]
            neighbors = []
            while len(neighbors) < k and len(self.nodes) > 1:
                candidate = choice(list(self.nodes.keys()))
                while candidate in neighbors:
                    candidate = choice(list(self.nodes.keys()))
                neighbors.append(candidate)

            for neighbor_id in neighbors:
                that_node = self.nodes[neighbor_id]
                edge_params = {"edge ID": None, "source": this_node, "target": that_node, "length": None}
                ed = Edge(edge_params)
                this_node.edges.update({ed.edge_id: ed})

            output += "Node with ID " + str(this_node.node_id) + " joined the network and connected to nodes"
            for neighbor_id in neighbors:
                output += ", " + str(neighbor_id)

            # Sync new node by copying a random neighbor

            neighbor_to_copy = choice(neighbors)
            this_node.block_dag = deepcopy(self.nodes[neighbor_to_copy].block_dag)

        return output

    def kill_node(self, event):
        #print("Beginning node death routine")
        output = ""
        #assert len(self.nodes) > 2
        node_id_to_kill = choice(list(self.nodes.keys()))
        node_to_kill = self.nodes[node_id_to_kill]

        record = []

        for node_id in self.nodes:
            this_node = self.nodes[node_id]
            for edge_id in this_node.edges:
                ed = this_node.edges[edge_id]
                if ed.target == node_to_kill:
                    new_neighbor_id = choice(list(self.nodes.keys()))
                    while new_neighbor_id == node_id_to_kill:
                        new_neighbor_id = choice(list(self.nodes.keys()))
                    new_neighbor = self.nodes[new_neighbor_id]
                    ed.target = new_neighbor
                    record.append(ed)
                    ed.incoming = []

        del self.nodes[node_id_to_kill]

        output += "Node with ID " + str(node_id_to_kill) + " left the network... replacing targets of edges"
        for ed in record:
            output += "," + str(ed.edge_id)
        output += ", with respective node IDs"
        for ed in record:
            output += "," + str(ed.target.node_id)

        return output

    def new_block(self, event):
        #print("Executing new block routine")
        output = ""
        assert event[:4] == "new,"
        node_id = int(event[4:])
        assert node_id in self.nodes
        node = self.nodes[node_id]
        b = node.find_block({"timestamp": self.clock})

        output += "Node with ID " + str(node_id) + " found a new block with block ID " + str(b.block_id) + " and timestamp "
        output += str(b.timestamp) + " and parents " + str(b.parents)
        return output

    def push_block(self, event):
        #print("Executing push block routine")
        output = ""
        assert event[:5] == "push,"
        [node_id, edge_id] = event[5:].split(",")
        node = self.nodes[int(node_id)]
        ed = node.edges[int(edge_id)]
        target_node_id = ed.target.node_id
        (dummy_t, new_block) = ed.push({"timestamp": self.clock})
        output += "Node with ID " + str(node_id) + " finished transmitting a block with block ID " + str(new_block.block_id)
        output += " and timestamp " + str(new_block.timestamp) + " and parents " + str(new_block.parents) + "across edge with ID "
        output += str(edge_id) + " to target node with ID " + str(target_node_id)

        return output


class TestGraph(unittest.TestCase):
    def test_graph(self):
        params = {"initial population": 25, "number of outgoing connections": 3, "simulation runtime":100.0}
        params.update({"birth rate": 1.0, "death rate":1.0})
        for i in range(10**3):
            G = Graph(params)
            G.run()


suite = unittest.TestLoader().loadTestsFromTestCase(TestGraph)
unittest.TextTestRunner(verbosity=1).run(suite)
