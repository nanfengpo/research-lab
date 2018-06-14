from random import *
from copy import *
from math import *
from Block import *
from BlockDAG import *


class Node(object):
    def __init__(self, inp):
        #                                 inp key : val
        #                               "node ID" : str
        #                            "clockshift" : float
        #                              "hashrate" : float
        #                             "edge dict" : dict
        ##                  "blockdag parameters" : dict
        ##             "difficulty update period" : int
        ##"target median inter-arrival wait time" : float
        ##                                "depth" : int
        self.block_dag = BlockDAG(inp["blockdag parameters"])
        inpp = deepcopy(inp)
        del inpp["blockdag parameters"]
        self.params = deepcopy(inpp)
        assert "hashrate" in self.params
        assert "clockshift" in self.params
        assert "edge dict" in self.params
        assert "blockdag parameters" not in self.params
        if inpp["node ID"] is None:
            self.node_id = hash(time() + random())
        else:
            self.node_id = deepcopy(inpp["node ID"])
        if "edge dict" in inp:
            self.edges = inpp["edge dict"]
        else:
            self.edges = {}

    def get_time(self):
        u = random()
        u = -1.0 * log(u)
        return u * self.block_dag.difficulty / self.params["hashrate"]

    def find_block(self, inp, relay=True):
        if len(inp) == 1:
            tprime = inp["timestamp"] + self.params["clockshift"]
            b = self.block_dag.generate_new_block({"timestamp": tprime})
        else:
            b = self.block_dag.new_block(inp)
        if relay:
            self.relay_block(b)
        return b

    def relay_block(self, b):
        for edge_id in self.edges:
            ed = self.edges[edge_id]
            delay = ed.length
            incoming_block_ids = [x[1].block_id for x in ed.incoming]
            if b.block_id not in incoming_block_ids:
                ed.incoming.append([delay, b])


class Edge(object):
    def __init__(self, inp):
        if inp["edge ID"] is None:
            self.edge_id = hash(time() + random())
        else:
            self.edge_id = deepcopy(inp["edge ID"])
        self.source = inp["source"]
        self.target = inp["target"]
        if inp["length"] is not None:
            self.length = inp["length"]
        else:
            self.length = 1.0  # Default mode. Random?
        self.incoming = []

    def push(self, inp):
        [dt, b] = [None, None]
        if self.incoming is not None:
            if len(self.incoming) > 0:
                for i in range(len(self.incoming)):
                    inc = self.incoming[i]
                    if inc[1].block_id == inp["block ID"]:
                        [dt,b] = inc
                        idx = i
                if len(self.incoming) > 1:
                    temp = self.incoming
                    left = temp[:idx]
                    right = temp[idx+1:]
                    self.incoming = left + right
                else:
                    self.incoming = []
                if b.block_id not in self.target.block_dag.blocks:
                    new_block_params = {"block ID": b.block_id, "timestamp": b.timestamp, "parents": b.parents}
                    self.target.find_block(new_block_params, relay=True)
        return [dt, b]


class TestNodesAndEdges(unittest.TestCase):
    def test_edges_and_nodes(self):
        block_dag_params = {"difficulty update period": 5, "target median inter-arrival wait time": 60.0, "depth": 3}
        node_params = {"node ID": None, "clockshift": 0.0, "hashrate": 1.0, "edge dict": {},
                       "blockdag parameters": block_dag_params}
        population = [Node(inp=node_params) for x in range(10)]
        ct = 25
        while ct > 0:
            x = choice(population)
            y = choice(population)
            while x == y:
                y = choice(population)
            edge_params = {"edge ID": None, "source": x, "target": y, "length": 1.0}
            ed = Edge(edge_params)
            assert ed.edge_id not in x.edges
            x.edges.update({ed.edge_id: ed})
            ct = ct - 1

        x = choice(population)
        inp = {"timestamp": 0.0}
        x.find_block(inp, relay=True)
        (dt,b) = ed.push(inp)

    def test_node(self):
        block_dag_params = {"difficulty update period": 5, "target median inter-arrival wait time": 60.0, "depth": 3}
        node_params = {"node ID": None, "clockshift": 0.0, "hashrate": 1.0, "edge dict": {},
                       "blockdag parameters": block_dag_params}
        real_block_interval = random() * block_dag_params["target median inter-arrival wait time"]
        nelly = Node(inp=node_params)

        ####
        t = [nelly.get_time() for x in range(10000)]
        tbar = sum(t) / 10000.0
        squaredmean = (tbar - 1.0) ** 2.0
        # print(squaredmean)
        self.assertTrue(squaredmean < .01)

        nelly.params["hashrate"] = 2.0
        t = [nelly.get_time() for x in range(10000)]
        tbar = sum(t) / 10000.0
        squaredmean = (tbar - 0.5) ** 2.0
        # print(squaredmean)
        self.assertTrue(squaredmean < .01)
        ####

        ## Genesis block ##

        start_time = time()
        this_time = start_time
        g = nelly.find_block({"timestamp": this_time}, relay=True)
        self.assertEqual(len(nelly.block_dag.blocks), 1)

        ## blocks a and b linearly

        this_time += real_block_interval
        a = nelly.find_block({"timestamp": this_time}, relay=True)
        self.assertEqual(len(nelly.block_dag.blocks), 2)
        this_time += real_block_interval
        b = nelly.find_block({"timestamp": this_time}, relay=True)
        self.assertEqual(len(nelly.block_dag.blocks), 3)

        ## blocks c and d fork
        this_time += real_block_interval
        new_block_params = {"block ID": None, "timestamp": this_time, "parents":[b.block_id]}
        c = nelly.find_block(new_block_params)
        d = nelly.find_block(new_block_params)

        this_time += real_block_interval
        new_block_params = {"block ID": None, "timestamp": this_time, "parents": list(nelly.block_dag.leaves.keys())}
        e = nelly.find_block(new_block_params)

        this_time += real_block_interval
        f = nelly.find_block({"timestamp": this_time}, relay=True)

suite = unittest.TestLoader().loadTestsFromTestCase(TestNodesAndEdges)
unittest.TextTestRunner(verbosity=1).run(suite)
