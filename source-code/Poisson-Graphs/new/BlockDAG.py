from copy import *
from random import *
import unittest
from Block import *
from collections import deque


class BlockDAG(object):
    def __init__(self, inp):
        self.blocks = {}  # {blockID:block}
        self.difficulty = 1.0
        self.leaves = {}  # {blockID:block}
        self.params = deepcopy(inp)

    def generate_new_block(self, inp):
        # inp = {"timestamp": float}
        timestamp = inp["timestamp"]
        parents = deepcopy(self.leaves)
        if len(parents) == 0:
            parents = None
        inpp = {"block ID": None, "timestamp": timestamp, "parents": parents}
        output = Block(inpp)
        self.add_block(output)
        return output

    def add_block(self, inp):
        valid_to_add = inp.block_id not in self.blocks
        if inp.parents is not None:
            for parentID in inp.parents:
                valid_to_add = valid_to_add and parentID in self.blocks
        if valid_to_add:
            self.blocks.update({inp.block_id: inp})
            self.leaves.update({inp.block_id: inp})
            # Make sure to remove parents from self.leaves
            if inp.parents is not None:
                for parentID in inp.parents:
                    if parentID in self.leaves:
                        del self.leaves[parentID]
            # Call updateDifficulty
            self.update_difficulty()

    def new_block(self, inp):
        # inp = {"block ID": str, "timestamp": float, "parents": list}
        new_block = Block(inp)
        self.add_block(new_block)
        return new_block

    def update_difficulty(self):
        if len(self.blocks) % self.params["difficulty update period"] == 0 and len(self.blocks) > 2:
            estimated_median = self.estimate()
            multiplicative_factor = self.params["target median inter-arrival wait time"] / estimated_median
            self.difficulty = multiplicative_factor * self.difficulty

    def estimate(self):
        obs = []  # To be filled with timestamps.
        q = deque()  # queue that will contain blockID and generation numbers.
        touched = []  # list of blockIDs that we have already thrown into obs or excluded
        for leafID in self.leaves:  # Fill queue with leaves...
            q.append((leafID, 0))  # ... which have "zero degrees of separation" from leaves.

        while len(q) > 0:  # Until the queue is empty...
            (x, j) = q.popleft()  # Take the next member of the queue.
            while len(q) > 0 and x in touched:  # Throw them away if we've dealt with them before.
                (x, j) = q.popleft()
            if x not in touched:
                obs.append(self.blocks[x].timestamp)
                touched.append(x)  # Include the timestamp and mark that we've touched this block
                if j + 1 < self.params["depth"]:
                    for parentID in self.blocks[x].parents:
                        if parentID not in touched:
                            q.append((parentID, j + 1))  # Put parents into the queue if they aren't too deep.

        order_stats = sorted(obs)  # Sort the timestamps
        # Compute the pairwise differences
        inter_arrival_times = [order_stats[k] - order_stats[k - 1] for k in range(1, len(order_stats))]
        sorted_inter_arrival_times = sorted(inter_arrival_times)  # Sort those too and then compute the median
        if len(sorted_inter_arrival_times) % 2 == 0:
            idx_one = len(sorted_inter_arrival_times) // 2 - 1
            idx_two = idx_one + 1
            median = (sorted_inter_arrival_times[idx_one] + sorted_inter_arrival_times[idx_two]) / 2.0
        else:
            idx = (len(sorted_inter_arrival_times) - 1) // 2
            median = sorted_inter_arrival_times[idx]
        return median


class TestBlockDAG(unittest.TestCase):
    def test_usage(self):
        print("Testing simplified usage")
        block_dag_params = {"difficulty update period": 5, "target median inter-arrival wait time": 60.0, "depth": 3}
        block_dag = BlockDAG(block_dag_params)

        genesis_block = block_dag.generate_new_block(inp={"timestamp": 0.0})
        a = block_dag.generate_new_block(inp={"timestamp": 1.0}) # auto-added
        b = block_dag.generate_new_block(inp={"timestamp": 2.0}) # auto-added
        c = block_dag.generate_new_block(inp={"timestamp": 3.0}) # auto-added
        d = block_dag.new_block({"block ID": None, "timestamp": 3.0, "parents": [b.block_id]})
        e = block_dag.new_block({"block ID": None, "timestamp": 4.0, "parents": [c.block_id, d.block_id]})
        f = block_dag.generate_new_block(inp={"timestamp":5.0})
        self.assertTrue(len(block_dag.blocks)==7)


    def test_bd(self):
        block_dag_params = {"difficulty update period": 5, "target median inter-arrival wait time": 60.0, "depth": 3}
        real_inter_arrival_time = random() * block_dag_params["target median inter-arrival wait time"]

        block_dag = BlockDAG(inp=block_dag_params)

        genesis_params = {"block ID": None, "timestamp": 0.0, "parents": None}
        g = Block(genesis_params)
        block_dag.add_block(g)

        self.assertEqual(len(block_dag.blocks), 1)
        self.assertTrue(g.block_id in block_dag.blocks and g.block_id in block_dag.leaves)
        self.assertEqual(block_dag.difficulty, 1.0)

        next_block_params = {"block ID": None, "timestamp": real_inter_arrival_time, "parents": [g.block_id]}
        b = Block(next_block_params)
        block_dag.add_block(b)

        self.assertEqual(len(block_dag.blocks), 2)
        tomato = b.block_id in block_dag.blocks and b.block_id in block_dag.leaves and g.block_id not in block_dag.leaves
        self.assertTrue(tomato)
        self.assertEqual(block_dag.difficulty, 1.0)

        next_block_params = {"block ID": None, "timestamp": 2.0 * real_inter_arrival_time, "parents": [b.block_id]}
        next_block = Block(next_block_params)
        block_dag.add_block(next_block)

        self.assertEqual(len(block_dag.blocks), 3)
        potato = next_block.block_id in block_dag.blocks and next_block.block_id in block_dag.leaves
        potato = potato and b not in block_dag.leaves
        self.assertTrue(potato)
        self.assertEqual(block_dag.difficulty, 1.0)

        next_block_params = {"block ID": None, "timestamp": 3.0 * real_inter_arrival_time}
        next_block_params.update({"parents": [next_block.block_id]})
        next_next_block = Block(next_block_params)
        block_dag.add_block(next_next_block)

        self.assertEqual(len(block_dag.blocks), 4)
        leek = next_next_block.block_id in block_dag.blocks and next_next_block.block_id in block_dag.leaves
        leek = leek and next_block not in block_dag.leaves
        self.assertTrue(leek)
        self.assertEqual(block_dag.difficulty, 1.0)

        next_block_params = {"block ID": None, "timestamp": 4.0 * real_inter_arrival_time}
        next_block_params.update({"parents": [next_next_block.block_id]})
        next_next_next_block = Block(next_block_params)
        block_dag.add_block(next_next_next_block)

        self.assertEqual(len(block_dag.blocks), 5)
        kohlrabi = next_next_next_block.block_id in block_dag.blocks and next_next_next_block.block_id in block_dag.leaves
        kohlrabi = kohlrabi and next_next_block not in block_dag.leaves
        self.assertTrue(kohlrabi)
        err = (block_dag.difficulty*real_inter_arrival_time - block_dag_params["target median inter-arrival wait time"])**2.0
        self.assertTrue(err < 1e-12)

        next_block_params = {"block ID": None, "timestamp": 5.0 * real_inter_arrival_time}
        next_block_params.update({"parents": [next_next_next_block.block_id]})
        next_next_next_next_block = Block(next_block_params)
        block_dag.add_block(next_next_next_next_block)

        self.assertEqual(len(block_dag.blocks), 6)
        beans = next_next_next_next_block.block_id in block_dag.blocks
        beans = beans and next_next_next_next_block.block_id in block_dag.leaves
        beans = beans and next_next_next_block not in block_dag.leaves
        self.assertTrue(beans)
        err = (real_inter_arrival_time*block_dag.difficulty-block_dag_params["target median inter-arrival wait time"])**2.0
        self.assertTrue(err < 1e-12)


suite = unittest.TestLoader().loadTestsFromTestCase(TestBlockDAG)
unittest.TextTestRunner(verbosity=1).run(suite)