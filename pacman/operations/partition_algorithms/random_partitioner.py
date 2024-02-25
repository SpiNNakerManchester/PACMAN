
from typing import Optional
from .abstract_partitioner import AbstractPartitioner
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import ApplicationGraph
from .solution_adopter import SolutionAdopter
import numpy as np
import random
class RandomPartitioner(AbstractPartitioner):
  
    def __init__(self, application_graph: ApplicationGraph = None):
        super().__init__(application_graph)

    def application_graph(self):
        return self._application_graph
    
    @overrides(AbstractPartitioner._adapted_output)
    def _adapted_output(self):
        return self.global_solution

    @overrides(AbstractPartitioner._partitioning)
    def _partitioning(self, max_slice_length = 100):
        # Begin coding for partitioning here
        N_Ai = [vertex.n_atoms for vertex in self.graph.vertices]
        N = np.sum(N_Ai)
        core_bits = np.ceil(np.log2(18))
        chip_bits = np.ceil(np.log2(N))
        chip_core_represent_total_length = chip_bits + core_bits
        bytes_needed_for_encoding = N * chip_core_represent_total_length
        self.global_solution = bytearray(bytes_needed_for_encoding)
        total_pos = 0
        for vertex in self.graph.vertices:
            n_atoms = vertex.n_atoms
            pos = 0
            while pos < n_atoms:
                slice_length = min(random.randint(0, max_slice_length), n_atoms - pos)
                if slice_length == 0:
                    continue
                random_chip = random.randint(0, N)
                random_core = random.randint(0, 17)
                chip_core_represent =  (random_chip << core_bits) | random_core
                binary_string = '{0:' + chip_core_represent_total_length + 'b}'.format(chip_core_represent) * slice_length
                global_offset_begin = (total_pos + pos) * chip_core_represent_total_length
                global_offset_end = (total_pos + pos + slice_length) * chip_core_represent_total_length - 1
                self.global_solution[global_offset_begin:global_offset_end] = binary_string
            total_pos += n_atoms                
        # End coding

        adapter_output = self._adapted_output()
        SolutionAdopter.AdoptSolution(adapter_output, self.graph, self.chip_counter)


