from copy import *
from random import *
import unittest
from time import *
from collections import *
from math import *
             
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
        '''
        Insert a new block if it isn't already included but all its parents are.
        '''
        validToAdd = inp.blockID not in self.blocks
        if inp.parents is not None:
            for parentID in inp.parents:
                validToAdd = validToAdd and parentID in self.blocks
        if validToAdd:
            self.blocks.update({inp.blockID:inp})
            self.leaves.update({inp.blockID:inp})
            # Make sure to remove parents from self.leaves
            if inp.parents is not None:
                for parentID in inp.parents:
                    if parentID in self.leaves:
                        del self.leaves[parentID]
            # Call updateDifficulty
            self.updateDifficulty()
            
    def updateDifficulty(self):
        '''
        Change difficulty according to estimate()
        '''
        if len(self.blocks) % self.params["difficulty update period"] == 0 and len(self.blocks) > 2:
            M = self.estimate()
            c = self.params["target median inter-arrival wait time"]/M
            self.difficulty = c*self.difficulty
        
    def estimate(self):
        '''
        Get median inter-arrival time from sorted list of all block timestamps 
        in the blockDAG, up to "depth" steps back from the leaves. 
        '''
        obs = []                              # To be filled with timestamps.
        q = deque()                           # queue that will contain blockID and generation numbers.
        touched = []                          # list of blockIDs that we have already thrown into obs or excluded
        for leafID in self.leaves:            # Fill queue with leaves...
            q.append((leafID, 0))             #         ... which have "zero degrees of separation" from leaves.
            
        while(len(q)>0):                      # Until the queue is empty...
            (x,j) = q.popleft()               # Take the next member of the queue.
            while(len(q)>0 and x in touched): # Throw them away if we've dealt with them before.
                (x,j) = q.popleft()
            if x not in touched:
                obs.append(self.blocks[x].timestamp)
                touched.append(x)             # Include the timestamp and mark that we've touched this block
                if j+1 < self.params["depth"]:
                    for parentID in self.blocks[x].parents:
                        if parentID not in touched:
                            q.append((parentID, j+1)) # Put parents into the queue if they aren't too deep.
                            
        orderStatistics = sorted(obs)         # Sort the timestamps
                                              # Compute the pairwise differences
        interArrivalTimes = [orderStatistics[k] - orderStatistics[k-1] for k in range(1,len(orderStatistics))]
        sortedInterArrivalTimes = sorted(interArrivalTimes) # Sort those too and then compute the median
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
       

class Node(object):
    '''
    Simulates a payment verifier on a cryptocurrency network.
    '''
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
        '''
        Spit out a random wait time dependent upon hash rate and difficulty.
        '''
        u = random()
        u = -1.0*log(u)
        return u*self.blockdag.difficulty/self.params["hashrate"]
        
    def findBlock(self, c, b=None, relay=True):
        '''
        Called with b=None means this node verified a brand new block, which must be constructed. Either way, relay.
        '''
        if b is None:
            blockParams = {"block ID":None, "timestamp": c + self.params["clockshift"], "parents":deepcopy(self.blockdag.leaves)}
            b = Block(blockParams)
        self.relayBlock(b, relay)
        return b
        
    def relayBlock(self, b, relay=True):
        '''
        Inserts a [timeUntilArrival, block] entry into each edge's incoming list
        '''
        self.blockdag.addBlock(b)
        if relay:
            for edgeID in self.edges:
                self.edges[edgeID].incoming.append([deepcopy(self.edges[edgeID].length), b])
            

class Edge(object):
    def __init__(self, inp):
        if inp["edge ID"] is None:
            self.edgeID = hash(time() + random())
        else:
            self.edgeID = deepcopy(inp["edge ID"])
        self.source = inp["source"]
        self.target = inp["target"]
        if inp["length"] is not None:
            self.length = inp["length"]
        else:
            self.length = 1.0 # Default mode. Random?
        self.incoming = []
        
    def push(self):
        dt = None
        if len(self.incoming)>0:
            self.incoming = sorted(self.incoming)
            [dt,b] = self.incoming[0]
            if len(self.incoming)>1:
                self.incoming = self.incoming[1:]
            else:
                self.incoming = []
                c=None
            self.target.findBlock(c, b, relay=True)
        return (dt,b)
        


class Test_Node(unittest.TestCase):
    def test_edges_and_nodes(self):
        nParams = {"hashrate":1.0, "clockshift":0.0}
        bdParams = {"difficulty update period":5, "target median inter-arrival wait time":60.0, "depth":3}
        realRate = random()*bdParams["target median inter-arrival wait time"]
        params = {"node ID":None, "blockdag parameters":bdParams, "edge dict":{}, "node parameters":nParams}
        
        population = [Node(inp=params) for x in range(10)]
        ct = 25
        while(ct > 0):
            x = choice(population)
            y = choice(population)
            while(x==y):
                y = choice(population)
            edgeParams = {"edge ID":None, "source":x, "target":y, "length":1.0}
            ed = Edge(edgeParams)
            assert ed.edgeID not in x.edges
            x.edges.update({ed.edgeID:ed})
            ct = ct - 1
            
        x = choice(population)
        x.findBlock(c=0.0,b=None, relay=True)
        dt=ed.push()
        
        
    def test_node(self):
        nParams = {"hashrate":1.0, "clockshift":0.0}
        bdParams = {"difficulty update period":5, "target median inter-arrival wait time":60.0, "depth":3}
        realRate = random()*bdParams["target median inter-arrival wait time"]
        params = {"node ID":None, "blockdag parameters":bdParams, "edge dict":{}, "node parameters":nParams}
        nelly = Node(inp=params)
        
        t  = [nelly.getTime() for x in range(10000)]
        tbar = sum(t)/10000.0
        squaredmean = (tbar - 1.0)**2.0
        #print(squaredmean)
        self.assertTrue(squaredmean < .01)
        
        nelly.params["hashrate"] = 2.0
        t  = [nelly.getTime() for x in range(10000)]
        tbar = sum(t)/10000.0
        squaredmean = (tbar - 0.5)**2.0
        #print(squaredmean)
        self.assertTrue(squaredmean < .01)
        
        startTime = time()
        thisTime = startTime
        nelly.findBlock(c=thisTime, b = None, relay=True)
        self.assertEqual(len(nelly.blockdag.blocks), 1)
        
        thisTime += realRate
        nelly.findBlock(c=thisTime, b = None, relay=True)
        self.assertEqual(len(nelly.blockdag.blocks), 2)
        
        thisTime += realRate
        blockparams = {"block ID":None,  "timestamp":thisTime, "parents":nelly.blockdag.leaves}
        bill = Block(blockparams)
        nelly.findBlock(c=thisTime, b=bill, relay=True) # c = anything here; bill has his timestamp already
        #print(nelly.blockdag.difficulty)
        self.assertEqual(len(nelly.blockdag.blocks),3)
        
        thisTime += realRate
        nelly.findBlock(c=thisTime, b=None, relay=True)
        #print(nelly.blockdag.difficulty)
        self.assertEqual(len(nelly.blockdag.blocks),4)
        
        thisTime += realRate
        nelly.findBlock(c=thisTime, b=None)
        #print(nelly.blockdag.difficulty)
        self.assertEqual(len(nelly.blockdag.blocks),5)
        self.assertTrue((nelly.blockdag.difficulty - bdParams["target median inter-arrival wait time"]/realRate)**2.0 < 1e-12)
        
        
                
suite = unittest.TestLoader().loadTestsFromTestCase(Test_Node)
unittest.TextTestRunner(verbosity=1).run(suite)
           
   
class Graph(object):
    def __init__(self, inp):
        self.nodes = {}
        self.clock = 0.0
        self.genesis = None
        self.params = deepcopy(inp)
        self._initialize()
        
    def _initialize(self):
        for i in range(self.params["initial population"]):
            nParams = {"hashrate":1.0, "clockshift":0.0}
            bdParams = {"difficulty update period":5, "target median inter-arrival wait time":60.0, "depth":3}
            params = {"node ID":None, "blockdag parameters":bdParams, "edge dict":{}, "node parameters":nParams}
            x = Node(inp=params)
            self.nodes.update({x.nodeID:x})
            
        k = self.params["number of outgoing connections"]
        for nodeID in self.nodes:
            thisNode = self.nodes[nodeID]
            neighbors = []
            while(len(neighbors) < k):
                candidate = choice(self.nodes)
                while(candidate in neighbors):
                    candidate = choice(self.nodes)
                neighbors.append(candidate)
                
            for neighborID in neighbors:
                thatNode = self.nodes[neighborID]
                edgeParams = {"edge ID":None, "source":thisNode, "target":thatNode, "length":None}
                ed = Edge(edgeParams)
                thisNode.edges.update({ed.edgeID:ed})
                
        # To avoid problems, we ensure everyone has the same genesis block at self.clock = 0.0
        genesisParams = {"block ID":None,  "timestamp":self.clock, "parents":None}
        self.genesis = Block(genesisParams)
        for nodeID in self.nodes:
            thisNode = self.nodes[nodeID]
            thisNode.findBlock(self.clock, self.genesis, relay=False)
          
            
    def run(self):
        with open("transcript.csv","w") as transcript:
            line = "dt,t,eventDescription\n"
            while(self.clock < self.params["simulation runtime"]):
                line = ""
            
                dt = (-1.0/self.params["birth rate"])*log(random())
                event = "birth"
                
                ds = (-1.0/self.params["death rate"])*log(random())
                if ds < dt:
                    dt = ds
                    event = "death"
                    
                for nid in self.nodes:
                    thisNode = self.nodes[nid]
                    ds = -1.0*thisNode.blockdag.difficulty*log(random())/thisNode.params["hashrate"]
                    if ds < dt:
                        dt = ds
                        event = "new," + str(nid)
                        
                    for eid in thisNode.edges:
                        ed = x.edges[eid]
                        if len(ed.incoming) > 0:
                            ed.incoming = sorted(ed.incoming)
                            [ds, b] = ed.incoming[0]
                            if ds < dt:
                                dt = ds
                                event = "push," + str(nid) + "," + str(eid)
                                
                line += str(dt) + ","
                self.clock += dt
                line += str(self.clock) + ","
                
                if event == "birth":
                    line += self.birthNode(event)
                elif event == "death":
                    line += self.killNode(event)
                elif event[:4] == "new,":
                    line += self.newBlock(event)
                elif event[:5] == "push,":
                    line += self.pushBlock(event)
                else:
                    line += "Bad output."
                    
                line += "\n"
                transcript.write(line)
                    
        return True
        
    def birthNode(self, event):
        output = ""
        
        nParams = {"hashrate":1.0, "clockshift":0.0}
        bdParams = {"difficulty update period":5, "target median inter-arrival wait time":60.0, "depth":3}
        params = {"node ID":None, "blockdag parameters":bdParams, "edge dict":{}, "node parameters":nParams}
        x = Node(inp=params)
        self.nodes.update({x.nodeID:x})
            
        k = self.params["number of outgoing connections"]
        neighbors = []
        while(len(neighbors) < k):
            candidate = choice(self.nodes)
            while(candidate in neighbors):
                candidate = choice(self.nodes)
            neighbors.append(candidate)
                
        for neighborID in neighbors:
            thatNode = self.nodes[neighborID]
            edgeParams = {"edge ID":None, "source":x, "target":thatNode, "length":None}
            ed = Edge(edgeParams)
            thisNode.edges.update({ed.edgeID:ed})
                
        output += "Node with ID " + str(x.nodeID) + " joined the network and connected to nodes"
        for neighborID in neighbors:
            output += ", " + neighborID
        
        # Sync new node by copying a random neighbor
        
        neighborToCopy = choice(neighbors)
        x.blockdag = deepcopy(self.nodes[neighborToCopy].blockdag)
        
        return output
        
    def killNode(self, event):
        output = ""
        
        nodeIDToKill = choice(self.nodes)
        nodeToKill = self.nodes[nodeIDToKill]
        
        record = []
        
        for nid in self.nodes:
            thisNode = self.nodes[nid]
            for eid in thisNode.edges:
                ed = thisNode.edges[eid]
                if ed.target == nodeToKill:
                    newNeighbor = choice(self.nodes)
                    while(newNeighbor == nodeToKill):
                        newNeighbor = choice(self.nodes)
                    ed.target = newNeighbor
                    record.append(ed)
                    ed.incoming = []
                    
        del self.nodes[nodeIDToKill]
        
        output += "Node with ID " + nodeIDToKill + " left the network... replacing targets of edges"
        for ed in record:
            output += "," + ed.edgeID
        output += ", with respective node IDs"
        for ed in record:
            output += "," + ed.target.nodeID
        
        return output
        
    def newBlock(self, event):
        output = ""
        assert event[:4] == "new,"
        nid = event[4:]
        node = self.nodes[nid]
        b = nid.findBlock(c=self.clock, b=None)
        
        output += "Node with ID " + nid + " found a new block with block ID " + b.blockID + " and timestamp " + b.timestamp + " and parents " + b.parents
        return output
        
    def pushBlock(self, event):
        output = ""
        assert event[:5] == "push,"
        [nid, eid] = event[5:].split(",")
        ed = self.edges[eid]
        targetID = ed.target.blockID
        (dummyT, newBlock) = ed.push()
        output += "Node with ID " + nid + " finished transmitting a block with block ID " + newBlock.blockID + " and timestamp " + newBlock.timestamp + " and parents " + newBlock.parents + "across edge with ID " + eid + " to target node with ID " + targetID 
        
        return output
        

class Test_Graph(unittest.TestCase):
    def test_graph(self):
        params = {"initial population":10, "number of outgoing connections":3, "birth rate":1.0, "death rate":1.0, "simulation runtime":100.0}
        G = Graph(params)
        G.run()

suite = unittest.TestLoader().loadTestsFromTestCase(Test_Node)
unittest.TextTestRunner(verbosity=1).run(suite)

