from random import *
from copy import *
from Block import *
from BlockDAG import *
from Node import *
from Graph import *

default_params = {"initial population": 3, "number of outgoing connections": 2, "simulation runtime": 100.0}
default_params.update({"birth rate": 0.1, "death rate": 0.001, "average edge length": 30.0})
default_params.update({"edge length dist": "poisson", "parent selection": "Bitcoin", "difficulty update period": 2016})
default_params.update({"target median inter-arrival wait time": 60000.0, "depth": 2016, "clockshift": 0.0, "hashrate": 1.0})


class Simulator(object):
    def __init__(self, params=default_params):
        self.params = deepcopy(params)

    def simulate(self):
        with open("transcript.csv", "w") as transcript:
            G = Graph(self.params)

            line = " #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####\n"
            transcript.write(line)
            line = "Beginning simulation with simulation parameters, " + str(self.params) + "\n"
            transcript.write(line)
            line = " #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####\n"
            transcript.write(line)
            line = "Describing initial state of network.\n"
            transcript.write(line)
            line = G.describe()
            transcript.write(line)
            line = " #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####\n"
            transcript.write(line)
            #line = "All blocks are starting with genesis block with ID, " + str(G.genesis["block ID"]) + "\n"
            #transcript.write(line)
            #line = " #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####\n"
            transcript.write(line)
            line = "Describing evolution of the network.\n"
            transcript.write(line)
            line = "t, event details\n"
            transcript.write(line)

            assert self.params["birth rate"] > 0.0
            assert self.params["death rate"] > 0.0

            while G.clock < self.params["simulation runtime"]:
                #print(G.clock)

                time_till_next_birth = (-1.0/self.params["birth rate"])*log(random())
                assert time_till_next_birth > 0.0

                time_till_next_death = (-1.0/self.params["death rate"])*log(random())
                assert time_till_next_death > 0.0

                time_till_next_new_block = None
                node_id_of_block_finder = None
                for node_id in G.nodes:
                    node = G.nodes[node_id]
                    next_diff = node.block_dag.next_difficulty
                    next_time_till_next_new_block = (-1.0*next_diff/node.params["hashrate"])*log(random())
                    if time_till_next_new_block is None or next_time_till_next_new_block < time_till_next_new_block:
                        time_till_next_new_block = next_time_till_next_new_block
                        node_id_of_block_finder = node_id
                assert time_till_next_new_block > 0.0
                assert node_id_of_block_finder in G.nodes

                time_till_next_block_push = None
                ids_of_block_push = None
                for node_id in G.nodes:
                    node = G.nodes[node_id]
                    for edge_id in node.edges:
                        ed = node.edges[edge_id]
                        if len(ed.incoming) > 0:
                            for arrival in ed.incoming:
                                next_time_till_next_block_push = arrival[0]
                                try:
                                    assert next_time_till_next_block_push > 0.0
                                except AssertionError:
                                    print("Next time till next block push: ", next_time_till_next_block_push)
                                next_ids_of_block_push = [node_id, edge_id]
                                if time_till_next_block_push is None or next_time_till_next_block_push < time_till_next_block_push:
                                    time_till_next_block_push = next_time_till_next_block_push
                                    ids_of_block_push = next_ids_of_block_push

                if time_till_next_block_push is None:
                    for node_id in G.nodes:
                        node = G.nodes[node_id]
                        for edge_id in node.edges:
                            ed = node.edges[edge_id]
                            assert len(ed.incoming) == 0
                    delta_t = min(time_till_next_birth, time_till_next_death, time_till_next_new_block)
                else:
                    assert time_till_next_block_push > 0.0
                    delta_t = min(time_till_next_birth, time_till_next_block_push, time_till_next_death, time_till_next_new_block)


                assert delta_t > 0.0
                G.roll_time(delta_t)
                assert G.clock > 0.0

                out = str(G.clock) + ", "
                executed = False
                if time_till_next_birth == delta_t:
                    #print("Birthing node.")
                    executed = True
                    out += G.birth_node()

                if time_till_next_death == delta_t:
                    if executed:
                        print("BOO")
                        out += "\nERROR: NON-POINT PROCESS\n"
                    else:
                        executed = True
                        #print("Killing node.")
                        out += G.kill_node()

                if time_till_next_new_block == delta_t:
                    if executed:
                        print("Boooooo")
                        out += "\nERROR: NON-POINT PROCESS\n"
                    else:
                        executed = True
                        #print("New block found.")
                        out += G.new_block(node_id_of_block_finder)

                if time_till_next_block_push == delta_t:
                    if executed:
                        print("Booo")
                        out += "\nERROR: NON-POINT PROCESS\n"
                    else:
                        executed = True
                        #print("Block pushed.")
                        out += G.push_blocks()

                out += "\n"
                transcript.write(out)

sally = Simulator(default_params)
sally.simulate()