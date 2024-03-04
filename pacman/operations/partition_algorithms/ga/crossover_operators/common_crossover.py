from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.crossover_operators.abst_crossover import AbstractGaCrossover

from spinn_utilities.overrides import overrides
from typing import Tuple
import random
import numpy as np

class CommonGaCrossoverPTypeKPoints(AbstractGaCrossover):
    def __init__(self, k: int) -> None:
        super().__init__()
        self._k = k

    @overrides(AbstractGaCrossover._do_crossover)
    def _do_crossover(self, individual1: AbstractGASolutionRepresentation, individual2: AbstractGASolutionRepresentation) -> Tuple[AbstractGaCrossover, AbstractGaCrossover]:
        individual1_ptype_rep = individual1.get_ptype_solution_representation()
        individual2_ptype_rep = individual2.get_ptype_solution_representation()
        single_neuron_encoding = individual1.get_single_neuron_encoding_length()

        if (len(individual1_ptype_rep) != len(individual2_ptype_rep)) or \
            (individual1.get_single_neuron_encoding_length() != individual2.get_single_neuron_encoding_length()) or \
                 (len(individual1_ptype_rep) % single_neuron_encoding != 0):
            raise ValueError

        neuron_count = len(individual1_ptype_rep) / single_neuron_encoding
        points = np.sort(random.sample(range(1, neuron_count - 1), k = self._k))
        new_individual1 = bytearray(single_neuron_encoding * neuron_count)
        new_individual2 = bytearray(single_neuron_encoding * neuron_count)
        parents = [individual1, individual2]
        previous_index = 0

        for p in points:
            neuron_encoding_begin = previous_index * single_neuron_encoding
            neuron_encoding_end = p * single_neuron_encoding
            new_individual1_select_parent_id = random.choice([0, 1])
            new_individual1[neuron_encoding_begin:neuron_encoding_end] = \
                parents[new_individual1_select_parent_id][neuron_encoding_begin:neuron_encoding_end]
            new_individual2[neuron_encoding_begin:neuron_encoding_end] = \
                parents[1 - new_individual1_select_parent_id][neuron_encoding_begin:neuron_encoding_end]

    def get_k(self):
        return self._k

    def __str__(self):
        return "comm_k_points"
    


class CommonGaCrossoverPTypeUniform(AbstractGaCrossover):
    def __init__(self) -> None:
        super().__init__()

    @overrides(AbstractGaCrossover._do_crossover)
    def _do_crossover(self, individual1: AbstractGASolutionRepresentation, individual2: AbstractGASolutionRepresentation) -> Tuple[AbstractGaCrossover, AbstractGaCrossover]:
        individual1_ptype_rep = individual1.get_ptype_solution_representation()
        individual2_ptype_rep = individual2.get_ptype_solution_representation()
        single_neuron_encoding = individual1.get_single_neuron_encoding_length()

        if (len(individual1_ptype_rep) != len(individual2_ptype_rep)) or \
            (individual1.get_single_neuron_encoding_length() != individual2.get_single_neuron_encoding_length()) or \
                 (len(individual1_ptype_rep) % single_neuron_encoding != 0):
            raise ValueError

        neuron_count = len(individual1_ptype_rep) / single_neuron_encoding
        new_individual1 = bytearray(single_neuron_encoding * neuron_count)
        new_individual2 = bytearray(single_neuron_encoding * neuron_count)
        parents = [individual1, individual2]

        for p in range(0, neuron_count):
            neuron_encoding_begin = p * single_neuron_encoding
            neuron_encoding_end = (p + 1) * single_neuron_encoding
            new_individual1_select_parent_id = random.choice([0, 1])
            new_individual1[neuron_encoding_begin:neuron_encoding_end] = \
                parents[new_individual1_select_parent_id][neuron_encoding_begin:neuron_encoding_end]
            new_individual2[neuron_encoding_begin:neuron_encoding_end] = \
                parents[1 - new_individual1_select_parent_id][neuron_encoding_begin:neuron_encoding_end]

    def __str__(self):
        return "comm_k_points"