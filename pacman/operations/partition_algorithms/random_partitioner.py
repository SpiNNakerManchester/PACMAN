
from typing import Optional
from .abstract_partitioner import AbstractPartitioner
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import ApplicationGraph
from .solution_adopter import SolutionAdopter
import numpy as np
import random
from pacman.utilities.utility_objs.chip_counter import ChipCounter
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamicsStructural)
class RandomPartitioner(AbstractPartitioner):
  
    def __init__(self, application_graph: ApplicationGraph = None, max_slice_length = 100, max_chips = -1, max_cores_per_chip = 18):
        super().__init__(application_graph)
        self._max_slice_length = max_slice_length
        self._max_chips = max_chips
        self._max_cores_per_chip = max_cores_per_chip

    def application_graph(self):
        return self._application_graph
    
    @overrides(AbstractPartitioner._adapted_output)
    def _adapted_output(self):
        return self.global_solution

    @overrides(AbstractPartitioner._partitioning)
    def _partitioning(self):
        # Begin coding for partitioning here
        N_Ai = [vertex.n_atoms for vertex in self.graph.vertices]
        N = int(np.sum(N_Ai))
        
        max_cores_per_chip = self._max_cores_per_chip
        max_chips = N if self._max_chips <= 0 else self._max_chips
        chip_core_represent_total_length = int(np.ceil(np.log2(max_chips * max_cores_per_chip)))
        bytes_needed_for_encoding = N * chip_core_represent_total_length
        self.global_solution = bytearray(bytes_needed_for_encoding)
        total_pos = 0
        neuron_in_core = dict({})
        for vertex in self.graph.vertices:
            n_atoms = vertex.n_atoms
            pos = 0
            while pos < n_atoms:
                slice_length = min(random.randint(0, self._max_slice_length), n_atoms - pos)
                if slice_length == 0:
                    continue
                random_chip = random.randint(0, max_chips - 1)
                random_core = random.randint(0, max_cores_per_chip - 1)
                location_key = "%d#%d" % (random_chip, random_core)
                if location_key in neuron_in_core:
                    neuron_in_core[location_key] = neuron_in_core[location_key] + slice_length
                else:
                    neuron_in_core[location_key] = slice_length

                chip_core_represent =  (random_chip * max_cores_per_chip) + random_core
                binary_string = ('{0:' + str(chip_core_represent_total_length) + 'b}').format(chip_core_represent) * slice_length
                global_offset_begin = (total_pos + pos) * chip_core_represent_total_length
                global_offset_end = (total_pos + pos + slice_length) * chip_core_represent_total_length - 1
                self.global_solution[global_offset_begin:global_offset_end + 1] = bytes(binary_string, 'ascii')
                pos += slice_length
            total_pos += n_atoms
        # End coding

        adapter_output = self._adapted_output()
        max_atoms_per_core = max(neuron_in_core.values())
        SolutionAdopter.AdoptSolution(adapter_output, self.graph, self.chip_counter, max_atoms_per_core=max_atoms_per_core)
