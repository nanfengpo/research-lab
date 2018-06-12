from copy import *
from random import *
import unittest
from time import *
from collections import *
             
 #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### 

class Block(object):
    def __init__(self, inp):
        if inp["block ID"] is None:
            self.blockID = hash(time() + random())
        else:
            self.blockID = deepcopy(inp["block ID"])
        self.timestamp = deepcopy(inp["timestamp"])
        self.parents = deepcopy(inp["parents"]) # list of block label/IDs
        
class BlockDAG(object):
    def __init__(self, inp):
        self.blocks = {} # {blockID:block}
        self.difficulty = 1.0
        self.leaves = {} # {blockID:block}
        self.params = deepcopy(inp) # {"target median inter-arrival rate":float, "difficulty update period":integer, "depth":integer}
        
    def addBlock(self, inp):
        validToAdd = inp.blockID not in self.blocks
        if inp.parents is not None:
            for parentID in inp.parents:
                validToAdd = validToAdd and parentID in self.blocks
        if validToAdd:
            self.blocks.update({inp.blockID:inp})
            self.leaves.update({inp.blockID:inp})
            if inp.parents is not None:
                for parentID in inp.parents:
                    if parentID in self.leaves:
                        del self.leaves[parentID]
            self.updateDifficulty()
            
    def updateDifficulty(self):
        if len(self.blocks) % self.params["difficulty update period"] == 0 and len(self.blocks) > 2:
            M = self.estimate()
            c = self.params["target median inter-arrival wait time"]/M
            self.difficulty = c*self.difficulty
        
    def estimate(self):
        obs = []
        q = deque()
        touched = []
        i = 0
        for leafID in self.leaves:
            q.append((leafID, i))
        while(len(q)>0):
            (x,j) = q.popleft()
            while(len(q)>0 and x in touched):
                (x,j) = q.popleft()
            if x not in touched:
                obs.append(self.blocks[x].timestamp)
                touched.append(x)
                if j+1 < self.params["depth"]:
                    for parentID in self.blocks[x].parents:
                        if parentID not in touched:
                            q.append((parentID, j+1))
        orderStatistics = sorted(obs)
        interArrivalTimes = [orderStatistics[k] - orderStatistics[k-1] for k in range(1,len(orderStatistics))]
        sortedInterArrivalTimes = sorted(interArrivalTimes)
        if len(sortedInterArrivalTimes) % 2 == 0:
            idxOne = len(sortedInterArrivalTimes)//2 - 1
            idxTwo = idxOne + 1
            median = (sortedInterArrivalTimes[idxOne] + sortedInterArrivalTimes[idxTwo])/2.0
        else:
            idx = (len(sortedInterArrivalTimes)-1)/2
            median = sortedInterArrivalTimes[idx]
        return median
            

class Test_BlockDAG(unittest.TestCase):
    def test_bd(self):
    
        bdParams = {"difficulty update period":5, "target median inter-arrival wait time":60.0, "depth":3}
        realRate = random()*bdParams["target median inter-arrival wait time"]
        
        bd = BlockDAG(inp=bdParams)
        
        genesisParams = {"block ID":None,  "timestamp":0.0, "parents":None}
        g = Block(genesisParams)
        bd.addBlock(g)
        
        self.assertEqual( len(bd.blocks), 1 )
        self.assertTrue(g.blockID in bd.blocks and g.blockID in bd.leaves)
        self.assertEqual(bd.difficulty, 1.0)
        
        nextBlockParams = {"block ID":None, "timestamp": realRate, "parents":[g.blockID]}
        b = Block(nextBlockParams)
        bd.addBlock(b)
        
        self.assertEqual( len(bd.blocks), 2 )
        self.assertTrue(b.blockID in bd.blocks and b.blockID in bd.leaves and g.blockID not in bd.leaves)
        self.assertEqual(bd.difficulty, 1.0)
        
        nextBlockParams = {"block ID":None, "timestamp": 2.0*realRate, "parents":[b.blockID]}
        nb = Block(nextBlockParams)
        bd.addBlock(nb)
        
        self.assertEqual( len(bd.blocks), 3 )
        self.assertTrue(nb.blockID in bd.blocks and nb.blockID in bd.leaves and b not in bd.leaves)
        self.assertEqual(bd.difficulty, 1.0)
        
        nextBlockParams = {"block ID":None, "timestamp": 3.0*realRate, "parents":[nb.blockID]}
        nnb = Block(nextBlockParams)
        bd.addBlock(nnb)
        
        self.assertEqual( len(bd.blocks), 4 )
        self.assertTrue(nnb.blockID in bd.blocks and nnb.blockID in bd.leaves and nb not in bd.leaves)
        self.assertEqual(bd.difficulty, 1.0)
        
        nextBlockParams = {"block ID":None, "timestamp": 4.0*realRate, "parents":[nnb.blockID]}
        nnnb = Block(nextBlockParams)
        bd.addBlock(nnnb)
        
        self.assertEqual( len(bd.blocks), 5 )
        self.assertTrue(nnnb.blockID in bd.blocks and nnnb.blockID in bd.leaves and nnb not in bd.leaves)
        self.assertEqual(bd.difficulty, bdParams["target median inter-arrival wait time"]/realRate)
        
        nextBlockParams = {"block ID":None, "timestamp": 5.0*realRate, "parents":[nnnb.blockID]}
        nnnnb = Block(nextBlockParams)
        bd.addBlock(nnnnb)
        
        self.assertEqual( len(bd.blocks), 6 )
        self.assertTrue(nnnnb.blockID in bd.blocks and nnnnb.blockID in bd.leaves and nnnb not in bd.leaves)
        self.assertEqual(bd.difficulty, bdParams["target median inter-arrival wait time"]/realRate)
        
        
                
suite = unittest.TestLoader().loadTestsFromTestCase(Test_BlockDAG)
unittest.TextTestRunner(verbosity=1).run(suite)

 #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####   
            
 #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### 


class Node(object):
    def __init__(self, inp):
        bdParams = inp["blockdag parameters"] # {"difficulty update period":5, "target median inter-arrival wait time":60.0, "depth":3}
        self.blockdag = BlockDAG(bdParams)
        if inp["node ID"] is None:
            self.nodeID = hash(time() + random())
        else:
            self.nodeID = deepcopy(inp["node ID"])
        if "edge dict" in inp:
            self.edges = inp["edge dict"]
        else:
            self.edges = {}
        self.params = deepcopy(inp["node parameters"]) # {"clockshift":float, "hashrate":float}
        
    def getTime(self):
        u = random()
        u = -1.0*log(u)
        return u*self.blockdag.difficulty/self.params["hashrate"]
        
    def findBlock(self, c, b=None):
        if b is None:
            blockParams = {"block ID":None, "timestamp": c + self.params["clockshift"], "parents":deepcopy(self.blockdag.leaves)}
            b = Block(blockParams)
        self.relayBlock(b)
        
    def relayBlock(self, b):
        self.blockdag.addBlock(b)
        for edgeID in self.edges:
            edges[edgeID].buffer.append([deepcopy(edges[edgeID].length), b])
            

class Test_Node(unittest.TestCase):
    def test_node(self):
        nParams = {"hashrate":1.0, "clockshift":1.1}
        bdParams = {"difficulty update period":5, "target median inter-arrival wait time":60.0, "depth":3}
        params = {"blockdag parameters":bdParams, "edge dict":{}, "node parameters":nParams}
        nelly = Node(inp=params)
        nelly.getTime()
        nelly.findBlock(c=time(),b=None)
        self.assertEqual(len(nelly.blockdag.blocks), 1)
        nelly.findBlock(c=time()+random(),b=None)
        self.assertEqual(len(nelly.blockdag.blocks),2)
        blockparams = {"block ID":None,  "timestamp":time() + 7.0*random(), "parents":nelly.blockdag.leaves}
        bill = Block(blockparams)
        nelly.findBlock(c=blockparams["timestamp"],b=bill)
        self.assertEqual(len(nelly.blockdag.blocks),3)
           
'''
class Edge(object):
    def __init__(self, inp):
        if inp["node ID"] is None:
            self.edgeID = hash(time() + random())
        else:
            self.edgeID = deepcopy(inp["edge ID"])
        self.source = inp["source"]
        self.target = inp["target"]
        self.incoming = []
        
    def push(self):
        self.incoming = sorted(self.incoming)
        [dt,b] = self.incoming[0]
        self.incoming = self.incoming[1:]
        self.target.findBlock(b)
        return dt
        
class Graph(object):
    def __init__(self, inp):
        self.nodes = {}
        self.params = deepcopy(inp)
        self._initialize()
        
    def addNode(self):
        newNode = Node(inp)
        
 '''
