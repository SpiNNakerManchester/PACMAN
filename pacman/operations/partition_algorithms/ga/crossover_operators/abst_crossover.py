from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from typing import Tuple

class AbstractGaCrossover(object):
    def do_crossover(self, individual1: AbstractGASolutionRepresentation, individual2: AbstractGASolutionRepresentation):
        # Currently limit the two crossover solution should in the same configurations of max_chips and max_cores_pre_chips.
        if individual1.get_single_neuron_encoding_length() != individual2.get_single_neuron_encoding_length() or individual1.get_max_chips() != individual2.get_max_chips() or individual1.get_max_cores_per_chip() != individual2.get_max_cores_per_chip():
            raise ValueError
        return self._do_crossover(individual1, individual2)
    
    def _do_crossover(self, individual1: AbstractGASolutionRepresentation, individual2: AbstractGASolutionRepresentation):
        raise NotImplementedError

    def __str__(self):
        return "abst_co"