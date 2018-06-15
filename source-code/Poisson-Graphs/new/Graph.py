from random import *
from copy import *
from Block import *
from BlockDAG import *
from Node import *

def get_poisson(lam):
    result = 0
    t = (-1.0/lam)*log(random())
    while t < 1.0:
        result += 1
        t += (-1.0/lam)*log(random())
    return result

class Graph(object):
    def __init__(self, inp):
        self.nodes = {}
        self.clock = 0.0
        self.params = deepcopy(inp)
        self.genesis = None
        self.genesis = self._initialize()

    def _initialize(self):
        for i in range(self.params["initial population"]):
            block_dag_params = {"difficulty update period": 5, "target median inter-arrival wait time": 60.0, "depth": 3, "parent selection": "Bitcoin"}
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
                if self.params["edge length dist"] == "poisson":
                    length = float(get_poisson(1.0/float(self.params["average edge length"])))
                else:
                    length = random()
                edge_params = {"edge ID": None, "source": this_node, "target": that_node, "length": length}
                ed = Edge(edge_params)
                this_node.edges.update({ed.edge_id: ed})

        # To avoid problems, we ensure everyone has the same genesis block at self.clock = 0.0
        genesis_params = {"block ID": None, "timestamp": self.clock, "parents": None, "difficulty": 1.0}
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
            line = "Describing initial state of network.\n"
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
            line = "dt,t,event_tag, details\n"
            #print(line)
            transcript.write(line)
            ct = 0
            while self.clock < self.params["simulation runtime"] and len(self.nodes) > 0:
                print(self.clock)
                ct += 1
                if ct % 1000 == 0:
                    print(ct, self.clock)
                line = ""

                dt = (-1.0 / self.params["birth rate"]) * log(random())
                event = "birth"
                print("Possible birth")

                ds = (-1.0 / self.params["death rate"]) * log(random())
                if ds < dt:
                    dt = ds
                    event = "death"
                    print("Possible death")

                for node_id in self.nodes:
                    this_node = self.nodes[node_id]
                    ds = this_node.get_time()
                    if ds < dt:
                        dt = ds
                        event = "new," + str(deepcopy(node_id))
                        print("Possible new block found")

                    for edge_id in this_node.edges:
                        ed = this_node.edges[edge_id]
                        if len(ed.incoming) > 0:
                            ed.incoming = sorted(ed.incoming, key=lambda x:x[0])
                            entry = ed.incoming[0]
                            ds = entry[0]
                            if ds < dt:
                                dt = ds
                                event = "push"# + str(deepcopy(node_id)) + "," + str(deepcopy(edge_id))
                                print("Possible relay of block")

                print("Rolling the clock forward, modifying wait time of all blocks on all edges")
                line += str(dt) + ", "
                self.clock += dt
                for node_id in self.nodes:
                    node = self.nodes[node_id]
                    for edge_id in node.edges:
                        ed = node.edges[edge_id]
                        for i in range(len(ed.incoming)):
                            ed.incoming[i][0] = ed.incoming[i][0] - dt
                            assert ed.incoming[i][0] >= 0.0
                line += str(self.clock) + ", "

                if event == "birth":
                    #print("Final event for this timestamp was a birth!")
                    line += "birth, " + self.birth_node(event)
                elif event == "death":
                    #print("Final event for this timestamp was a death!")
                    line += "death, " + self.kill_node(event)
                elif event[:4] == "new,":
                    #print("Final event for this timestamp was discovery of a new block!")
                    line += "new_block, " + self.new_block(event)
                elif event == "push":
                    transcript_entry = "["
                    for node_id in self.nodes:
                        node = self.nodes[node_id]
                        for edge_id in node.edges:
                            ed = node.edges[edge_id]
                            if ed.incoming is not None:
                                if len(ed.incoming) > 0:
                                    for i in range(len(ed.incoming)):
                                        if i < len(ed.incoming):
                                            inc = ed.incoming[i]
                                            assert inc[1].block_id in node.block_dag.blocks
                                            if inc[0] <= 0.0:
                                                next_event = "push," + str(node_id) + "," + str(edge_id) + "," + str(inc[1].block_id)
                                                transcript_entry += self.push_block(next_event) + ", "
                    transcript_entry += "]"
                    line += "push_block, " + transcript_entry
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
        k = self.params["number of outgoing connections"]
        output = ""
        if event is not None:
            block_dag_params = {"difficulty update period": 5, "target median inter-arrival wait time": 60.0, "depth": 3, "parent selection": "Bitcoin"}
            node_params = {"node ID": None, "clockshift": 0.0, "hashrate": 1.0, "edge dict": {}, "blockdag parameters": block_dag_params}
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

            output += "Node with ID " + str(this_node.node_id) + " joined the network and connected to nodes"
            for edge_id in this_node.edges:
                ed = this_node.edges[edge_id]
                neighbor = ed.target
                output += ", " + str(neighbor.node_id)
            output += ", and with respective edge IDs, "
            for edge_id in this_node.edges:
                output += ", " + str(edge_id)



            # Sync new node by copying a random neighbor

            neighbor_to_copy = choice(neighbors)
            this_node.block_dag = deepcopy(neighbor_to_copy.block_dag)

            output += ", and bootstraps the blockdag by copying neighbor with node ID, "
            output += str(neighbor_to_copy.node_id)
        #print("Exiting node birth routine")
        return output

    def kill_node(self, event):
        #print("Beginning node death routine")
        output = ""
        if len(self.nodes) > 1:
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
                output += ", " + str(ed.edge_id)
            output += ", with respective node IDs"
            for ed in record:
                output += ", " + str(ed.target.node_id)
        else:
            output += "Kill node = network extinction. No action taken."
        #print("Exiting node kill routine")
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
        if b.parents is not None:
            parent_list = str(b.parents)
        else:
            parent_list = "None"
        output += str(b.timestamp) + " and parents " + parent_list
        #print("Exiting new block routine")
        return output

    def push_block(self, event):
        output = ""

        [node_id, edge_id, block_id] = event[5:].split(",")
        node_id  =  int(node_id)
        edge_id  =  int(edge_id)
        block_id = int(block_id)
        assert node_id in self.nodes
        node = self.nodes[node_id]
        assert edge_id in node.edges
        ed = node.edges[edge_id]
        assert block_id in node.block_dag.blocks
        assert block_id in [x[1].block_id for x in ed.incoming]
        block = node.block_dag.blocks[block_id]
        target_node_id = ed.target.node_id
        target_node = self.nodes[target_node_id]

        for i in range(len(ed.incoming)):
            inc = ed.incoming[i]
            if inc[1].block_id == block_id:
                [dummy_t, new_block] = ed.push({"timestamp": self.clock, "block ID": block_id})
                break

        output += "Node with ID " + str(node_id) + " finished transmitting a block with block ID " + str(new_block.block_id)
        output += " and timestamp " + str(new_block.timestamp) + " and parents "
        if new_block.parents is not None:
            output += str(new_block.parents)
        else:
            output += "None"
        output += " across edge with ID " + str(edge_id) + " to target node with ID " + str(target_node_id)
        #print("Exiting push block routine")
        return output


class TestGraph(unittest.TestCase):
    def test_graph_run(self):
        params = {"initial population": 25, "number of outgoing connections": 3, "simulation runtime": 100.0}
        params.update({"birth rate": 1.0, "death rate": 1.0, "average edge length": 30.0, "edge length dist": "poisson"})
        G = Graph(params)

        #### #### ###
        # Test initialization
        for node_id in G.nodes:
            node = G.nodes[node_id]
            self.assertEqual(len(node.block_dag.blocks), 1)
            for edge_id in node.edges:
                ed = node.edges[edge_id]
                self.assertEqual(len(ed.incoming), 0)

        G.run()

    def test_graph_actions(self):
        params = {"initial population": 25, "number of outgoing connections": 3, "simulation runtime": 100.0}
        params.update({"birth rate": 1.0, "death rate": 1.0, "average edge length": 30.0, "edge length dist": "poisson"})
        G = Graph(params)

        #### #### ###
        # Test initialization
        for node_id in G.nodes:
            node = G.nodes[node_id]
            self.assertEqual(len(node.block_dag.blocks), 1)
            for edge_id in node.edges:
                ed = node.edges[edge_id]
                self.assertEqual(len(ed.incoming),0)

        #### #### ####
        # Test new_block
        x = G.nodes[choice(list(G.nodes.keys()))]
        neighbors = [x.edges[edge_id].target for edge_id in x.edges]
        event = "new," + str(deepcopy(x.node_id))
        num_blocks_before = len(x.block_dag.blocks)
        print(G.new_block(event))
        num_blocks_after = len(x.block_dag.blocks)
        self.assertEqual(num_blocks_after - num_blocks_before,1)
        touched_edges = list(x.edges.keys())

        edge_arrivals = []
        for node_id in G.nodes:
            node = G.nodes[node_id]
            for edge_id in node.edges:
                ed = node.edges[edge_id]
                if len(ed.incoming)>0:
                    for item in ed.incoming:
                        edge_arrivals.append(item)

        self.assertEqual(len(edge_arrivals), G.params["number of outgoing connections"])

        #### #### ####
        # Test push_block
        y = x.edges[choice(list(x.edges.keys()))]
        self.assertTrue(len(y.incoming)>0)
        inc = y.incoming[0]
        event = "push," + str(deepcopy(x.node_id)) + "," + str(deepcopy(y.edge_id)) + "," + str(inc[1].block_id)
        z = y.target
        num_blocks_before = len(z.block_dag.blocks)
        self.assertEqual(len(z.block_dag.blocks),1)
        for edge_id in z.edges:
            ed = z.edges[edge_id]
            if edge_id not in touched_edges:
                self.assertEqual(len(ed.incoming), 0)
            else:
                self.assertEqual(len(ed.incoming), 1)
        print(G.push_block(event))
        num_blocks_after = len(z.block_dag.blocks)
        self.assertEqual(num_blocks_after - num_blocks_before,1)
        for edge_id in z.edges:
            ed = z.edges[edge_id]
            self.assertEqual(len(ed.incoming), 1)

        #### #### ####
        # test kill_node
        num_nodes = len(G.nodes)
        event = "death"
        print(G.kill_node(event))
        self.assertEqual(num_nodes - len(G.nodes), 1)

        #### #### ####
        # test birth_node
        num_nodes = len(G.nodes)
        event = "birth"
        print(G.birth_node(event))
        self.assertEqual(len(G.nodes) - num_nodes, 1)

suite = unittest.TestLoader().loadTestsFromTestCase(TestGraph)
unittest.TextTestRunner(verbosity=1).run(suite)
