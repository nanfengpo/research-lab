from copy import *
from random import *
import unittest
from Block import *
from collections import deque


class BlockDAG(object):
    def __init__(self, inp):
        self.blocks = {}  # {blockID:block}
        self.next_difficulty = 1.0
        self.leaves = {}  # {blockID:block}
        self.params = deepcopy(inp)

    def generate_new_block(self, inp):
        """
        Take as input some inp and present as output a block. This is the case when the node generates a new honest
        block, using the local subset of the leaf set as the parent set.

        Usage: generate_new_block({"block ID": None, "timestamp": time(), "parents": list(self.leaves.keys())})

        :param inp: {"block ID": int, "timestamp": float, "parents": list}
        :return output: Block({"block ID": None, "timestamp": inp["timestamp", "parents": self.leaves}
        """
        # inp = {"timestamp": float}
        timestamp = inp["timestamp"]
        parents = []
        if len(self.leaves)==0:
            parents = None
        elif len(self.leaves)==1:
            parents = deepcopy(list(self.leaves.keys()))
        elif self.params["parent selection"]=="Bitcoin":
            options = deepcopy(list(self.leaves.keys()))
            results = []
            q = deque()
            #print(options)
            for opt in options:
                this_block = self.blocks[opt]
                s = this_block.difficulty
                if this_block.parents is not None:
                    if len(this_block.parents) > 0:
                        for parent_id in this_block.parents:
                            q.append(parent_id)
                while len(q) > 0:
                    next_id = q.popleft()
                    next_block = self.blocks[next_id]
                    s += next_block.difficulty
                    if next_block.parents is not None:
                        if len(next_block.parents) > 0:
                            for parent_id in next_block.parents:
                                q.append(parent_id)
                results.append([s, opt])
            #print(results)
            results = sorted(results, key=lambda x:x[0])
            i = 1
            next_candidate = results[-1]
            top_score = next_candidate[0]
            candidates = []
            while next_candidate[0] == top_score:
                candidates.append(next_candidate)
                i += 1
                next_candidate = results[-i]
            if len(candidates) > 1:
                parents = [choice(candidates)]
            else:
                parents = [candidates[0]]
        elif self.params["parent selection"]=="Spectre":
            parents = deepcopy(list(self.leaves.keys()))

        inpp = {"block ID": None, "timestamp": timestamp, "parents": parents, "difficulty": deepcopy(self.next_difficulty)}
        output = Block(inpp)
        self.add_block(output)

        return output

    def add_block(self, inp):
        # inp is a Block()
        valid_to_add = inp.block_id not in self.blocks
        if inp.parents is not None:
            for parentID in inp.parents:
                if parentID not in self.blocks:
                    valid_to_add = False
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
        if "difficulty" not in inp:
            inp.update({"difficulty": self.next_difficulty})
        new_block = Block(inp)
        self.add_block(new_block)
        return new_block

    def update_difficulty(self):
        estimated_median = self.estimate()
        if estimated_median is not None:
            if estimated_median > 0.0:
                multiplicative_factor = self.params["target median inter-arrival wait time"] / estimated_median
                if self.params["parent selection"]=="Bitcoin":
                    if len(self.blocks) % self.params["difficulty update period"] == 0 and len(self.blocks) > 2:
                        self.next_difficulty = multiplicative_factor * self.next_difficulty
                    else:
                        pass
                else:
                    self.next_difficulty = multiplicative_factor * self.next_difficulty

    def estimate(self):
        # Returns median inter-arrival time
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
                    if self.blocks[x].parents is not None:
                        for parentID in self.blocks[x].parents:
                            if parentID not in touched:
                                q.append((parentID, j + 1))  # Put parents into the queue if they aren't too deep.
        #print("Observations = ", str(obs))
        order_stats = sorted(obs)  # Sort the timestamps)
        #print("Order statistics = ", str(order_stats))
        median = None
        if len(order_stats) >= 2:
            # Compute the pairwise differences
            inter_arrival_times = [order_stats[k] - order_stats[k - 1] for k in range(1, len(order_stats))]
            #print("Inter-arrival times = ", str(inter_arrival_times))
            sorted_inter_arrival_times = sorted(inter_arrival_times)  # Sort those too and then compute the median
            #print("Sorted inter-arrival times = " + str(sorted_inter_arrival_times))

            assert len(sorted_inter_arrival_times) >= 1

            if len(sorted_inter_arrival_times)==1:
                median = sorted_inter_arrival_times[0]
            elif len(sorted_inter_arrival_times)>1:
                if len(sorted_inter_arrival_times) % 2 == 0:
                    idx_one = len(sorted_inter_arrival_times) // 2 - 1
                    idx_two = idx_one + 1
                    median = (sorted_inter_arrival_times[idx_one] + sorted_inter_arrival_times[idx_two]) / 2.0
                else:
                    idx = (len(sorted_inter_arrival_times) - 1) // 2
                    median = sorted_inter_arrival_times[idx]
        #print("Median = ", str(median))
        return median


class TestBlockDAG(unittest.TestCase):
    def test_usage(self):
        #print("Testing simplified usage")
        block_dag_params = {"difficulty update period": 5, "target median inter-arrival wait time": 60.0, "depth": 3}
        block_dag_params.update({"parent selection": "Bitcoin"})
        block_dag = BlockDAG(block_dag_params)

        genesis_block = block_dag.generate_new_block(inp={"timestamp": 0.0})
        a = block_dag.generate_new_block(inp={"timestamp": 1.0}) # auto-added
        b = block_dag.generate_new_block(inp={"timestamp": 2.0}) # auto-added
        c = block_dag.generate_new_block(inp={"timestamp": 3.0}) # auto-added
        d = block_dag.new_block({"block ID": None, "timestamp": 3.1, "parents": [b.block_id], "difficulty": block_dag.next_difficulty})
        e = block_dag.new_block({"block ID": None, "timestamp": 4.0, "parents": [c.block_id, d.block_id], "difficulty": block_dag.next_difficulty})
        f = block_dag.generate_new_block(inp={"timestamp": 5.0})
        self.assertTrue(len(block_dag.blocks)==7)

    def test_generate_new_block(self):
        block_dag_params = {"difficulty update period": 5, "target median inter-arrival wait time": 60.0, "depth": 3}
        block_dag_params.update({"parent selection": "Bitcoin"})
        block_dag = BlockDAG(block_dag_params)

        self.assertEqual(len(block_dag.blocks), 0)
        self.assertEqual(len(block_dag.leaves), 0)
        genesis_block = block_dag.generate_new_block(inp={"timestamp": 0.0})
        self.assertEqual(len(block_dag.blocks), 1)
        self.assertTrue(genesis_block.block_id in block_dag.blocks)
        self.assertEqual(len(block_dag.leaves), 1)
        self.assertTrue(genesis_block.block_id in block_dag.leaves)
        self.assertEqual(block_dag.next_difficulty, 1.0)

        test_parent_set = [genesis_block.block_id]
        a = block_dag.generate_new_block(inp={"timestamp": 1.0})  # auto-added
        self.assertEqual(len(block_dag.blocks), 2)
        self.assertEqual(len(block_dag.leaves), 1)
        self.assertTrue(a.block_id in block_dag.leaves)
        self.assertFalse(genesis_block.block_id in block_dag.leaves)
        self.assertEqual(a.timestamp, 1.0)
        self.assertEqual(a.parents, test_parent_set)
        self.assertEqual(a.difficulty, block_dag.next_difficulty)

        test_parent_set = [a.block_id]
        b = block_dag.generate_new_block(inp={"timestamp": 2.0})  # auto-added
        self.assertEqual(len(block_dag.blocks), 3)
        self.assertEqual(len(block_dag.leaves), 1)
        self.assertTrue(b.block_id in block_dag.leaves)
        self.assertFalse(a.block_id in block_dag.leaves)
        self.assertEqual(b.timestamp, 2.0)
        self.assertEqual(b.parents, test_parent_set)
        self.assertEqual(b.difficulty, block_dag.next_difficulty)

        test_parent_set = [b.block_id]
        c = block_dag.generate_new_block(inp={"timestamp": 3.0})  # auto-added
        self.assertEqual(len(block_dag.blocks), 4)
        self.assertEqual(len(block_dag.leaves), 1)
        self.assertTrue(c.block_id in block_dag.leaves)
        self.assertFalse(b.block_id in block_dag.leaves)
        self.assertEqual(c.timestamp, 3.0)
        self.assertEqual(c.parents, test_parent_set)
        self.assertEqual(c.difficulty, block_dag.next_difficulty)

        test_parent_set = [c.block_id]
        d = block_dag.generate_new_block(inp={"timestamp": 4.0})  # auto-added
        self.assertEqual(len(block_dag.blocks), 5)
        self.assertEqual(len(block_dag.leaves), 1)
        self.assertTrue(d.block_id in block_dag.leaves)
        self.assertFalse(c.block_id in block_dag.leaves)
        self.assertEqual(d.timestamp, 4.0)
        self.assertEqual(d.parents, test_parent_set)
        self.assertFalse(d.difficulty == block_dag.next_difficulty)
        self.assertFalse(block_dag.next_difficulty == 1.0)
        self.assertTrue((block_dag.next_difficulty/block_dag_params["target median inter-arrival wait time"] - 1.0)**2 < 1e-12)

        ## Test spectre

        block_dag_params = {"difficulty update period": 5, "target median inter-arrival wait time": 60.0, "depth": 3}
        block_dag_params.update({"parent selection": "Spectre"})
        block_dag = BlockDAG(block_dag_params)
        dT = block_dag.params["target median inter-arrival wait time"]

        genesis_block = block_dag.generate_new_block(inp={"timestamp": 0.0})
        self.assertEqual(genesis_block.difficulty, 1.0)
        test_parent_set = [genesis_block.block_id]
        old_diff = block_dag.next_difficulty
        #print("Next difficulty = " + str(block_dag.next_difficulty))

        a = block_dag.generate_new_block(inp={"timestamp": dT})  # auto-added
        self.assertEqual(a.difficulty, 1.0)
        self.assertEqual(a.timestamp, dT)
        self.assertEqual(a.parents, test_parent_set)
        self.assertEqual(block_dag.next_difficulty, 1.0*old_diff)
        self.assertTrue(len(block_dag.blocks), 2)
        old_diff = block_dag.next_difficulty


        b = block_dag.new_block({"block ID": None, "timestamp": 3.0*dT, "parents": test_parent_set, "difficulty": block_dag.next_difficulty})
        self.assertEqual(b.timestamp, 3.0*dT)
        self.assertEqual(b.parents, a.parents)
        self.assertEqual(b.parents, test_parent_set)
        #print("block_dag.next_difficulty = ", str(block_dag.next_difficulty))
        self.assertEqual(block_dag.next_difficulty, 1.0/1.5*old_diff)
        self.assertTrue(len(block_dag.blocks), 3)
        old_diff = block_dag.next_difficulty

        test_parent_set = [a.block_id, b.block_id]
        #print("Incoming problematic stuff")
        c = block_dag.new_block({"block ID": None, "timestamp": 4.0*dT, "parents": test_parent_set, "difficulty": block_dag.next_difficulty})
        self.assertEqual(c.timestamp, 4.0*dT)
        self.assertEqual(c.parents, test_parent_set)
        self.assertEqual(block_dag.next_difficulty, 1.0*old_diff)
        self.assertTrue(len(block_dag.blocks), 4)
        old_diff = block_dag.next_difficulty

        d = block_dag.new_block({"block ID": None, "timestamp": 6.0*dT, "parents": test_parent_set, "difficulty": block_dag.next_difficulty})
        next_diff = block_dag.next_difficulty
        self.assertEqual(next_diff / old_diff, 1.0/1.5)
        self.assertEqual(d.timestamp, 6.0*dT)
        self.assertEqual(d.parents, test_parent_set)
        self.assertEqual(d.parents, c.parents)
        self.assertEqual(block_dag.next_difficulty, 1.0/1.5*old_diff)
        self.assertTrue(len(block_dag.blocks), 5)





    def test_bd(self):
        block_dag_params = {"difficulty update period": 5, "target median inter-arrival wait time": 60.0, "depth": 3}
        block_dag_params.update({"parent selection": "Bitcoin"})
        real_inter_arrival_time = random() * block_dag_params["target median inter-arrival wait time"]

        block_dag = BlockDAG(inp=block_dag_params)

        genesis_params = {"block ID": None, "timestamp": 0.0, "parents": None, "difficulty": 1.0}
        g = Block(genesis_params)
        block_dag.add_block(g)

        self.assertEqual(len(block_dag.blocks), 1)
        self.assertTrue(g.block_id in block_dag.blocks and g.block_id in block_dag.leaves)
        self.assertEqual(block_dag.next_difficulty, 1.0)

        next_block_params = {"block ID": None, "timestamp": real_inter_arrival_time, "parents": [g.block_id], "difficulty": 1.0}
        b = Block(next_block_params)
        block_dag.add_block(b)

        self.assertEqual(len(block_dag.blocks), 2)
        tomato = b.block_id in block_dag.blocks and b.block_id in block_dag.leaves and g.block_id not in block_dag.leaves
        self.assertTrue(tomato)
        self.assertEqual(block_dag.next_difficulty, 1.0)

        next_block_params = {"block ID": None, "timestamp": 2.0 * real_inter_arrival_time, "parents": [b.block_id], "difficulty": 1.0}
        next_block = Block(next_block_params)
        block_dag.add_block(next_block)

        self.assertEqual(len(block_dag.blocks), 3)
        potato = next_block.block_id in block_dag.blocks and next_block.block_id in block_dag.leaves
        potato = potato and b not in block_dag.leaves
        self.assertTrue(potato)
        self.assertEqual(block_dag.next_difficulty, 1.0)

        next_block_params = {"block ID": None, "timestamp": 3.0 * real_inter_arrival_time, "difficulty": 1.0}
        next_block_params.update({"parents": [next_block.block_id]})
        next_next_block = Block(next_block_params)
        block_dag.add_block(next_next_block)

        self.assertEqual(len(block_dag.blocks), 4)
        leek = next_next_block.block_id in block_dag.blocks and next_next_block.block_id in block_dag.leaves
        leek = leek and next_block not in block_dag.leaves
        self.assertTrue(leek)
        self.assertEqual(block_dag.next_difficulty, 1.0)

        next_block_params = {"block ID": None, "timestamp": 4.0 * real_inter_arrival_time, "difficulty": 1.0}
        next_block_params.update({"parents": [next_next_block.block_id]})
        next_next_next_block = Block(next_block_params)
        block_dag.add_block(next_next_next_block)

        self.assertEqual(len(block_dag.blocks), 5)
        kohlrabi = next_next_next_block.block_id in block_dag.blocks and next_next_next_block.block_id in block_dag.leaves
        kohlrabi = kohlrabi and next_next_block not in block_dag.leaves
        self.assertTrue(kohlrabi)
        err = (block_dag.next_difficulty*real_inter_arrival_time - block_dag_params["target median inter-arrival wait time"])**2.0
        self.assertTrue(err < 1e-12)

        next_block_params = {"block ID": None, "timestamp": 5.0 * real_inter_arrival_time, "difficulty": 1.0}
        next_block_params.update({"parents": [next_next_next_block.block_id]})
        next_next_next_next_block = Block(next_block_params)
        block_dag.add_block(next_next_next_next_block)

        self.assertEqual(len(block_dag.blocks), 6)
        beans = next_next_next_next_block.block_id in block_dag.blocks
        beans = beans and next_next_next_next_block.block_id in block_dag.leaves
        beans = beans and next_next_next_block not in block_dag.leaves
        self.assertTrue(beans)
        err = (real_inter_arrival_time*block_dag.next_difficulty-block_dag_params["target median inter-arrival wait time"])**2.0
        self.assertTrue(err < 1e-12)


suite = unittest.TestLoader().loadTestsFromTestCase(TestBlockDAG)
unittest.TextTestRunner(verbosity=1).run(suite)