from random import *
from copy import *
from Block import *
from BlockDAG import *
from Node import *
from Graph import *

params = {"initial population": 25, "number of outgoing connections": 10, "simulation runtime": 10000.0}
params.update({"birth rate": 0.1, "death rate": 0.001, "average edge length": 30.0})
params.update({"edge length dist": "poisson", "parent selection": "Bitcoin", "difficulty update period": 2016})
params.update({"target median inter-arrival wait time": 60000.0, "depth": 2016, "clockshift": 0.001, "hashrate": 1.0})
G = Graph(params)
G.run()