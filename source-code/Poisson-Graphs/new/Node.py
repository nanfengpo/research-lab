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
        assert "blockdag parameters" not in self.params
        if "node ID" in inpp:
            if inpp["node ID"] is None:
                self.node_id = hash(time() + random())
            else:
                self.node_id = deepcopy(inpp["node ID"])
        else:
            self.node_id = hash(time() + random())
        if "edge dict" in inp:
            self.edges = inpp["edge dict"]
        else:
            self.edges = {}

    def get_time(self):
        u = random()
        u = -1.0 * log(u)
        return u * self.block_dag.next_difficulty / self.params["hashrate"]

    def find_block(self, inp, relay=True, genesis=False):
        if not genesis:
            assert inp["timestamp"] > 0.0
        if len(inp) == 1:
            tprime = inp["timestamp"]
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
            assert delay > 0.0
            if len(ed.incoming) > 0:
                incoming_block_ids = [x[1].block_id for x in ed.incoming]
                if b.block_id not in incoming_block_ids and b.block_id not in ed.target.block_dag.blocks:
                    ed.incoming.append([delay, b])
            else:
                ed.incoming.append([delay, b])




class Edge(object):
    def __init__(self, inp):
        if "edge ID" in inp:
            if inp["edge ID"] is None:
                self.edge_id = hash(time() + random())
            else:
                self.edge_id = deepcopy(inp["edge ID"])
        else:
            self.edge_id = hash(time() + random())
        self.source = inp["source"]
        self.target = inp["target"]
        if inp["length"] is not None:
            self.length = inp["length"]
        else:
            self.length = 1.0  # Default mode. Random?
        self.incoming = []

    def push_all(self):
        result = None
        if self.incoming is not None:
            if len(self.incoming) > 0:
                new_incoming = []
                for entry in self.incoming:
                    inc_time = entry[0]
                    inc_block = entry[1]
                    if inc_time == 0.0:
                        result = inc_block.block_id
                        if inc_block.block_id not in self.target.block_dag.blocks:
                            find_block_inp = {"block ID": inc_block.block_id, "timestamp": inc_block.timestamp, "parents": inc_block.parents}
                            self.target.find_block(find_block_inp, relay=True)
                    else:
                        new_incoming.append([inc_time, inc_block])
                self.incoming = deepcopy(new_incoming)
        for entry in self.incoming:
            assert entry[0] > 0.0
        return result


class TestNodesAndEdges(unittest.TestCase):
    def test_node_first(self):
        block_dag_params = {"difficulty update period": 5, "target median inter-arrival wait time": 60.0, "depth": 3, "parent selection": "Bitcoin"}
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
        new_block_params = {"block ID": None, "timestamp": this_time, "parents":[b.block_id], "difficulty": nelly.block_dag.next_difficulty}
        c = nelly.find_block(new_block_params)
        d = nelly.find_block(new_block_params)

        this_time += real_block_interval
        new_block_params = {"block ID": None, "timestamp": this_time, "parents": list(nelly.block_dag.leaves.keys()), "difficulty": nelly.block_dag.next_difficulty}
        e = nelly.find_block(new_block_params)

        this_time += real_block_interval
        f = nelly.find_block({"timestamp": this_time}, relay=True)

    def test_node_detail(self):
        # Test initialization
        test_blockdag_params = {"difficulty update period": 5, "target median inter-arrival wait time": 60.0, "depth": 3}
        test_blockdag_params.update({"parent selection": "Bitcoin"})
        inp = {"node ID": None, "clockshift": 1.0, "hashrate": 1.0, "edge dict": {}}
        inp.update({"blockdag parameters": test_blockdag_params, "difficulty update period":test_blockdag_params["difficulty update period"]})
        inp.update({"target median inter-arrival wait time": test_blockdag_params["target median inter-arrival wait time"], "depth": test_blockdag_params["depth"]})

        nelly = Node(inp)
        self.assertEqual(len(nelly.block_dag.blocks),0)
        self.assertEqual(nelly.params["hashrate"], inp["hashrate"])
        self.assertTrue(nelly.params["clockshift"], inp["clockshift"])
        self.assertEqual(nelly.params["edge dict"], inp["edge dict"])

        #### Test get_time
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

        #### Test find_block
        n = len(nelly.block_dag.blocks)
        genesis_block = nelly.find_block(inp={"block ID": None, "timestamp": 0.0, "parents": None}, relay=False)
        self.assertEqual(len(nelly.block_dag.blocks) - n, 1)
        self.assertTrue(genesis_block.block_id in nelly.block_dag.blocks)
        self.assertTrue(genesis_block.block_id in nelly.block_dag.leaves)
        self.assertEqual(len(nelly.block_dag.blocks), 1)
        self.assertEqual(len(nelly.block_dag.leaves), 1)
        n = len(nelly.block_dag.blocks)

        a = nelly.find_block(inp={"block ID": None, "timestamp": 1.0, "parents": [genesis_block.block_id]}, relay=False)
        self.assertEqual(len(nelly.block_dag.blocks) - n, 1)
        self.assertTrue(a.block_id in nelly.block_dag.blocks)
        self.assertTrue(a.block_id in nelly.block_dag.leaves)
        self.assertFalse(genesis_block.block_id in nelly.block_dag.leaves)
        self.assertEqual(len(nelly.block_dag.blocks), 2)
        self.assertEqual(len(nelly.block_dag.leaves), 1)
        n = len(nelly.block_dag.blocks)

        b = nelly.find_block(inp={"block ID": None, "timestamp": 2.0, "parents": [a.block_id]}, relay=False)
        self.assertEqual(len(nelly.block_dag.blocks) - n, 1)
        self.assertTrue(b.block_id in nelly.block_dag.blocks)
        self.assertTrue(b.block_id in nelly.block_dag.leaves)
        self.assertFalse(a.block_id in nelly.block_dag.leaves)
        self.assertEqual(len(nelly.block_dag.blocks), 3)
        self.assertEqual(len(nelly.block_dag.leaves), 1)

    def test_node_and_edge(self):
        test_blockdag_params = {"difficulty update period": 5, "target median inter-arrival wait time": 60.0, "depth": 3}
        test_blockdag_params.update({"parent selection": "Bitcoin"})
        inp = {"node ID": None, "clockshift": 1.0, "hashrate": 1.0, "edge dict": {}}
        inp.update({"blockdag parameters": test_blockdag_params, "difficulty update period": test_blockdag_params["difficulty update period"]})
        inp.update({"target median inter-arrival wait time": test_blockdag_params["target median inter-arrival wait time"], "depth": test_blockdag_params["depth"]})

        alice = Node(inp)
        bob = Node(inp)

        edge_params = {"edge ID": None, "source": alice, "target": bob, "length": 30.0}
        ed = Edge(edge_params)
        alice.edges.update({ed.edge_id: ed})
        genesis_block = alice.find_block(inp={"block ID": None, "timestamp": 0.0, "parents": None}, relay=True, genesis=True)
        self.assertTrue(len(ed.incoming)==1)
        [dt, b] = ed.incoming[0]
        self.assertEqual(genesis_block.block_id, b.block_id)
        self.assertFalse(genesis_block.block_id in bob.block_dag.blocks)
        ed.incoming[0][0] = 0.0
        # print(ed.incoming)
        ed.push_all()
        self.assertTrue(len(ed.incoming)==0)
        self.assertTrue(genesis_block.block_id in bob.block_dag.blocks)

        a = alice.find_block(inp={"block ID": None, "timestamp": 1.0, "parents": [genesis_block.block_id]}, relay=True)
        self.assertTrue(len(ed.incoming)==1)
        b = alice.find_block(inp={"block ID": None, "timestamp": 2.0, "parents": [a.block_id]}, relay=True)
        self.assertTrue(len(ed.incoming)==2)
        ed.incoming[0][0] = 0.0
        ed.push_all()
        self.assertTrue(len(ed.incoming)==1)


suite = unittest.TestLoader().loadTestsFromTestCase(TestNodesAndEdges)
unittest.TextTestRunner(verbosity=1).run(suite)
