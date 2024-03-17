
from .abstract_partitioner import AbstractPartitioner
from spinn_utilities.overrides import overrides
from .solution_adopter import SolutionAdopter
import numpy as np
import random
from pacman.operations.partition_algorithms.ga.entities.resource_configuration import ResourceConfiguration
class RandomPartitioner(AbstractPartitioner):
    def __init__(self, max_slice_length = 100, resource_constraint_configuration: ResourceConfiguration = None):
        super().__init__(resource_constraint_configuration)
        self._max_slice_length = max_slice_length

    def get_resource_constraint_configuration(self) -> ResourceConfiguration:
        return self._resource_constraint_configuration
    
    @overrides(AbstractPartitioner._adapted_output)
    def _adapted_output(self):
        return self.global_solution

    @overrides(AbstractPartitioner._partitioning)
    def _partitioning(self):
        # Begin coding for partitioning here
        N_Ai = [vertex.n_atoms for vertex in self._graph.vertices]
        N = int(np.sum(N_Ai))
        
        max_cores_per_chip = self.get_resource_constraint_configuration().get_max_cores_per_chip()
        max_chips = N if self.get_resource_constraint_configuration().get_max_chips() <= 0 else self.get_resource_constraints_configuration().get_max_chips()
        chip_core_represent_total_length = int(np.ceil(np.log2(max_chips * max_cores_per_chip)))
        bytes_needed_for_encoding = N * chip_core_represent_total_length
        self.global_solution = bytearray(bytes_needed_for_encoding)
        total_pos = 0
        neuron_in_core = dict({})
        for vertex in self._graph.vertices:
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
                chip_core_location_int_encoding =  (random_chip * max_cores_per_chip) + random_core
                binary_string = ('{0:' + str(chip_core_represent_total_length) + 'b}').format(chip_core_location_int_encoding) * slice_length
                global_offset_begin = (total_pos + pos) * chip_core_represent_total_length
                global_offset_end = (total_pos + pos + slice_length) * chip_core_represent_total_length - 1
                self.global_solution[global_offset_begin:global_offset_end + 1] = bytes(binary_string, 'ascii')
                pos += slice_length
            total_pos += n_atoms
        # End coding

        adapter_output = self._adapted_output()
        SolutionAdopter.AdoptSolution(adapter_output, self._graph, self._chip_counter, self.get_resource_constraint_configuration())