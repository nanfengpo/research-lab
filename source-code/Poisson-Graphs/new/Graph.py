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
                    length = float(get_poisson(1.0/float(self.params["average edge length"])))
                else:
                    length = random()
                edge_params = {"source": this_node, "target": that_node, "length": length}
                ed = Edge(edge_params)
                this_node.edges.update({ed.edge_id: ed})
                assert ed.source.node_id in self.nodes
                assert ed.target.node_id in self.nodes
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
            good_to_go = True
            old_clock = deepcopy(self.clock)
            while self.clock < self.params["simulation runtime"] and len(self.nodes) > 0 and good_to_go:
                print(old_clock)
                ct += 1
                if ct % 1000 == 0:
                    print(ct, self.clock)

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
                        #print("Possible new block found")

                    for edge_id in this_node.edges:
                        ed = this_node.edges[edge_id]
                        if len(ed.incoming) > 0:
                            ed.incoming = sorted(ed.incoming, key=lambda x:x[0])
                            entry = ed.incoming[0]
                            ds = entry[0]
                            if ds < dt:
                                dt = ds
                                event = "push," + str(deepcopy(node_id)) + "," + str(deepcopy(edge_id)) + "," + str(deepcopy(entry[1].block_id))
                                #print("Possible relay of block")

                #print("Rolling the clock forward, modifying wait time of all blocks on all edges")
                line += str(dt) + ", "
                print("dt = ", dt)
                assert dt > 0.0
                self.clock += dt
                print(self.clock)
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
                elif event[:3] == "new":
                    #print("Final event for this timestamp was discovery of a new block!")
                    line += "new_block, " + self.new_block(event)
                elif event[:4] == "push":
                    #print("Final event for this timestamp was a push!")
                    line += self.push_block(event)
                else:
                    line += "Bad output."

                line += "\n"
                transcript.write(line)
                #print(line)
                if self.clock <= old_clock:
                    good_to_go = False
                else:
                    old_clock = deepcopy(self.clock)
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
        b = node.find_block({"timestamp": self.clock}, relay=True)

        output += "Node with ID, " + str(node_id) + ", found a new block with block ID, " + str(b.block_id) + ", and timestamp "
        if b.parents is not None:
            parent_list = str(b.parents)
        else:
            parent_list = "None"
        output += str(b.timestamp) + ", and parents, " + parent_list
        #print("Exiting new block routine")
        return output

    def push_block(self, event):
        event = event.split(",")
        node_id = int(event[1])
        edge_id = int(event[2])
        block_id = int(event[3])
        node = self.nodes[node_id]
        ed = self.edges[edge_id]
        temp_inc = []
        for entry in ed.incoming:
            if entry[1].block_id != block_id:
                temp_inc.append(entry)
            else:
                block_dat = {"block ID": block_id, "timestamp": entry[1].timestamp, "parents": entry[1].parents}
                ed.target.find_block(block_dat)
        ed.incoming = deepcopy(temp_inc)
        output = "Edge with ID, " + str(edge_id) + ", delivers block with ID, " + str(block_id) + ", to node ID, "
        output += str(ed.target.node_id) + ", from node ID, " + str(node_id) + "\n"
        return output


class TestGraph(unittest.TestCase):
    def test_graph_run(self):
        params = {"initial population": 25, "number of outgoing connections": 3, "simulation runtime": 10000.0}
        params.update({"birth rate": 1.0, "death rate": 1.0, "average edge length": 30.0})
        params.update({"edge length dist": "poisson", "parent selection": "Bitcoin", "difficulty update period": 5})
        params.update({"target median inter-arrival wait time": 60.0, "depth": 3, "clockshift": 0.0, "hashrate": 1.0})
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
        params = {"initial population": 3, "number of outgoing connections": 2, "simulation runtime": 10000.0}
        params.update({"birth rate": 1.0, "death rate": 1.0, "average edge length": 30.0})
        params.update({"edge length dist": "poisson", "parent selection": "Bitcoin", "difficulty update period": 5})
        params.update({"target median inter-arrival wait time": 60.0, "depth": 3, "clockshift": 0.0, "hashrate": 1.0})
        G = Graph(params)

        #### #### ###
        # Test initialization
        for node_id in G.nodes:
            node = G.nodes[node_id]
            self.assertEqual(len(node.block_dag.blocks), 1)
            for edge_id in node.edges:
                ed = node.edges[edge_id]
                self.assertEqual(len(ed.incoming), 0)
                self.assertTrue(ed.source.node_id in G.nodes)
                self.assertTrue(ed.target.node_id in G.nodes)
                #print("Edge = ", str(ed.source.node_id), ", ", str(ed.target.node_id))

        #### #### ####
        # Notation and prerequisites
        #### #### ####
        # Pick three random distinct nodes (there are only 3 in total! this is all of them, we are just labeling
        nids = list(G.nodes.keys())
        x = G.nodes[choice(list(G.nodes.keys()))]
        y = G.nodes[choice(list(G.nodes.keys()))]
        while y.node_id == x.node_id:
            y = G.nodes[choice(list(G.nodes.keys()))]
        z = G.nodes[choice(list(G.nodes.keys()))]
        while z.node_id == x.node_id or z.node_id == y.node_id:
            z = G.nodes[choice(list(G.nodes.keys()))]
        self.assertTrue(x.node_id != y.node_id)
        self.assertTrue(x.node_id != z.node_id)
        self.assertTrue(y.node_id != z.node_id)
        nids = [x.node_id, y.node_id, z.node_id]
        for edge_id in x.edges:
            ed = x.edges[edge_id]
            self.assertTrue(ed.source.node_id in nids)
            self.assertTrue(ed.target.node_id in nids)

        # Get the list of edge_id from each node
        x_edge_list = list(x.edges.keys())
        y_edge_list = list(y.edges.keys())
        z_edge_list = list(z.edges.keys())

        # Each has outgoing connections = 2, so the network is totally connected. Each edge has two keys.
        x_edge_key_one = x_edge_list[0]
        x_edge_key_two = x_edge_list[1]
        #print("Keys = ", x_edge_key_one, x_edge_key_two)

        y_edge_key_one = y_edge_list[0]
        y_edge_key_two = y_edge_list[1]

        z_edge_key_one = z_edge_list[0]
        z_edge_key_two = z_edge_list[1]

        # Initialize as "None" the variables we'll be using as shorthand for our edges
        xy = None
        xz = None
        yx = None
        yz = None
        zx = None
        zy = None

        #print(x.node_id, y.node_id, z.node_id, x.edges[x_edge_key_one].target.node_id, x.edges[x_edge_key_two].target.node_id, y.edges[y_edge_key_one].target.node_id, y.edges[y_edge_key_two].target.node_id, z.edges[z_edge_key_one].target.node_id, z.edges[z_edge_key_two].target.node_id)

        # Set xy and xz
        bad_assignment = False
        if x.edges[x_edge_key_one].target.node_id == y.node_id:
            xy = x.edges[x_edge_key_one]
            xz = x.edges[x_edge_key_two]
        elif x.edges[x_edge_key_one].target.node_id == z.node_id:
            xy = x.edges[x_edge_key_two]
            xz = x.edges[x_edge_key_one]
        else:
            bad_assignment = True
        self.assertFalse(bad_assignment)

        # Set yx and yz
        bad_assignment = False
        if y.edges[y_edge_key_one].target.node_id == x.node_id:
            yx = y.edges[y_edge_key_one]
            yz = y.edges[y_edge_key_two]
        elif y.edges[y_edge_key_one].target.node_id == z.node_id:
            yx = y.edges[y_edge_key_two]
            yz = y.edges[y_edge_key_one]
        else:
            bad_assignment = True
        self.assertFalse(bad_assignment)

        bad_assignment = False
        if z.edges[z_edge_key_one].target.node_id == x.node_id:
            zx = z.edges[z_edge_key_one]
            zy = z.edges[z_edge_key_two]
        elif z.edges[z_edge_key_one].target.node_id == y.node_id:
            zx = z.edges[z_edge_key_two]
            zy = z.edges[z_edge_key_one]
        else:
            bad_assignment = True
        self.assertFalse(bad_assignment)

        #### #### ####
        # Test that notations and pre-requisites was not degenerate.
        self.assertTrue(xy is not None)
        self.assertTrue(xz is not None)
        self.assertTrue(yx is not None)
        self.assertTrue(yz is not None)
        self.assertTrue(zx is not None)
        self.assertTrue(zy is not None)

        # Set edge lengths.
        x.edges[xy.edge_id].length = 10.0
        x.edges[xz.edge_id].length = 15.0
        y.edges[yx.edge_id].length = 7.0
        y.edges[yz.edge_id].length = 17.0
        z.edges[zx.edge_id].length = 13.0
        z.edges[zy.edge_id].length = 2.0
        self.assertEqual(xy.length, 10.0)
        self.assertEqual(xz.length, 15.0)
        self.assertEqual(yx.length, 7.0)
        self.assertEqual(yz.length, 17.0)
        self.assertEqual(zx.length, 13.0)
        self.assertEqual(zy.length, 2.0)

        # We are going to spawn a block at x
        num_blocks_before = len(x.block_dag.blocks)
        event = "new," + str(deepcopy(x.node_id))
        new_block_event = G.new_block(event) # inserts to xy and xz also
        new_block_event = new_block_event.split(",")
        new_block_id = int(new_block_event[3])
        num_blocks_after = len(x.block_dag.blocks)
        self.assertEqual(num_blocks_after - num_blocks_before, 1)
        self.assertEqual(len(x.block_dag.blocks), 2)
        self.assertTrue(new_block_id in x.block_dag.blocks)
        self.assertEqual(len(xy.incoming), 1)
        self.assertEqual(len(xz.incoming), 1)
        self.assertEqual(len(yx.incoming), 0)
        self.assertEqual(len(yz.incoming), 0)
        self.assertEqual(len(zx.incoming), 0)
        self.assertEqual(len(zy.incoming), 0)

        # Then we roll time forward min(xy.length, xz.length)
        dt = min(xy.length, xz.length)
        self.assertEqual(dt, xy.length) # verify edge xy
        self.assertTrue(dt > 0.0)
        for entry in xy.incoming:
            entry[0] = entry[0] - dt
        for entry in xz.incoming:
            entry[0] = entry[0] - dt

        # And we push_block off xy to y
        num_blocks_before = len(y.block_dag.blocks)
        self.assertEqual(num_blocks_before, 1)
        push_block_event = G.push_block()
        #print("Push block event = ", push_block_event)
        num_blocks_after = len(y.block_dag.blocks)
        self.assertEqual(num_blocks_after - num_blocks_before, 1)
        self.assertEqual(len(yz.incoming), 1)
        self.assertEqual(len(yx.incoming), 0)

        #### #### ####
        # test kill_node
        num_nodes = len(G.nodes)
        event = "death"
        death_event = G.kill_node(event)
        #print(death_event)
        self.assertEqual(num_nodes - len(G.nodes), 1)

        #### #### ####
        # test birth_node
        num_nodes = len(G.nodes)
        event = "birth"
        birth_event = G.birth_node(event)
        #print(birth_event)
        self.assertEqual(len(G.nodes) - num_nodes, 1)

    def test_usage(self):
        params = {"initial population": 25, "number of outgoing connections": 3, "simulation runtime": 10000.0}
        params.update({"birth rate": 1.0, "death rate": 1.0, "average edge length": 30.0})
        params.update({"edge length dist": "poisson", "parent selection": "Bitcoin", "difficulty update period": 5})
        params.update({"target median inter-arrival wait time": 60.0, "depth": 3, "clockshift": 0.0, "hashrate": 1.0})
        G = Graph(params)
        G.run()
        print("Run completed)")


#suite = unittest.TestLoader().loadTestsFromTestCase(TestGraph)
#unittest.TextTestRunner(verbosity=1).run(suite)
