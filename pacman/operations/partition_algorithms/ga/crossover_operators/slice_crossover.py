from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.crossover_operators.abst_crossover import AbstractGaCrossover
from pacman.operations.partition_algorithms.ga.solution_representations.common_ga_solution_representation import CommonGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_representations.slice_representation import GASliceSolutionRepresentation

from spinn_utilities.overrides import overrides
from typing import Tuple
import random
import numpy as np

# class CommonGaCrossoverKPoints(AbstractGaCrossover):
#     def __init__(self, k: int, use_ptype=True) -> None:
#         super().__init__()
#         self._k = k
#         self._use_ptype = use_ptype

#     @overrides(AbstractGaCrossover._do_crossover)
#     def _do_crossover(self, individual1: AbstractGASolutionRepresentation, individual2: AbstractGASolutionRepresentation) -> Tuple[AbstractGaCrossover, AbstractGaCrossover]:
#         if not isinstance(individual1, GASliceSolutionRepresentation) or not isinstance(individual2, GASliceSolutionRepresentation):
#             raise TypeError
#         individual1_rep = individual1.get_ptype_solution_representation() if self._use_ptype else individual1.get_gtype_solution_representation()
#         individual2_rep = individual2.get_ptype_solution_representation() if self._use_ptype else individual2.get_gtype_solution_representation()
#         single_neuron_encoding_length = individual1.get_single_neuron_encoding_length()

#         if (len(individual1_rep) != len(individual2_rep)) or \
#             (individual1.get_single_neuron_encoding_length() != individual2.get_single_neuron_encoding_length()) or \
#                 (not self._use_ptype or (len(individual1_rep) % single_neuron_encoding_length != 0)):
#             raise ValueError

#         neuron_count = (len(individual1_rep) / single_neuron_encoding_length) if self._use_ptype else len(individual1_rep)
#         max_cores_per_chip = individual1.get_max_cores_per_chip()
#         max_chips = individual1.get_max_chips()
#         points = np.sort(random.sample(range(1, neuron_count - 1), k = self._k))
#         new_individual1 = bytearray(single_neuron_encoding_length * neuron_count) if self._use_ptype else [0] * neuron_count
#         new_individual2 = bytearray(single_neuron_encoding_length * neuron_count) if self._use_ptype else [0] * neuron_count
#         parents = [individual1, individual2]
#         previous_index = 0
#         if not self._use_ptype:
#             single_neuron_encoding_length = 1

#         for p in points:
#             neuron_encoding_begin = previous_index * single_neuron_encoding_length
#             neuron_encoding_end = p * single_neuron_encoding_length
#             new_individual1_select_parent_id = random.choice([0, 1])
#             new_individual1[neuron_encoding_begin:neuron_encoding_end] = \
#                 parents[new_individual1_select_parent_id][neuron_encoding_begin:neuron_encoding_end]
#             new_individual2[neuron_encoding_begin:neuron_encoding_end] = \
#                 parents[1 - new_individual1_select_parent_id][neuron_encoding_begin:neuron_encoding_end]

#         return (CommonGASolutionRepresentation(new_individual1, max_cores_per_chip, max_chips, self._use_ptype), CommonGASolutionRepresentation(new_individual2, max_cores_per_chip, max_chips, self._use_ptype))
    
#     def get_k(self):
#         return self._k

#     def __str__(self):
#         return "comm_k_points"
    


class GaSliceCrossoverUniform(AbstractGaCrossover):
    def __init__(self, k: int, use_ptype=True) -> None:
        super().__init__()
        self._k = k
        self._use_ptype = use_ptype

    @overrides(AbstractGaCrossover._do_crossover)
    def _do_crossover(self, individual1: AbstractGASolutionRepresentation, individual2: AbstractGASolutionRepresentation) -> Tuple[AbstractGaCrossover, AbstractGaCrossover]:
        if not isinstance(individual1, GASliceSolutionRepresentation) or not isinstance(individual2, GASliceSolutionRepresentation):
            raise TypeError
        individual1_rep = individual1.get_gtype_solution_representation()
        individual2_rep = individual2.get_gtype_solution_representation()
        # last element should be neuron_count - 1. Two solutions should cover the same count of neurons.
        if(individual1_rep[-1] != individual2_rep[-1]):
            raise ValueError
        individual1_length = len(individual1_rep)
        individual2_length = len(individual2_rep)
        individuals = [individual1_rep, individual2_rep]
        P = [0, 0]
        new_individual1 = [[], [], []]
        new_individual2 = [[], [], []]
        SLICE_TO_INDEX = 1
        SLICE_CHIP_INDEX = 2
        SLICE_CORE_INDEX =3
        while P[0] < individual1_length and P[1] < individual2_length:
            select_individual = random.choices([0, 1], k = 1)[0]
            
            new_individual1[0].append(individuals[select_individual][P[select_individual]][SLICE_TO_INDEX])
            new_individual1[1].append(individuals[select_individual][P[select_individual]][SLICE_CHIP_INDEX])
            new_individual1[2].append(individuals[select_individual][P[select_individual]][SLICE_CORE_INDEX])

            P[select_individual] += 1
            while individuals[1 - select_individual][P[1 - select_individual]] < individuals[select_individual][P[select_individual]]:
                new_individual2[0].append(individuals[1 - select_individual][P[1 - select_individual]][SLICE_TO_INDEX])
                new_individual2[1].append(individuals[1 - select_individual][P[1 - select_individual]][SLICE_CHIP_INDEX])
                new_individual2[2].append(individuals[1 - select_individual][P[1 - select_individual]][SLICE_CORE_INDEX])
                P[1 - select_individual] += 1
        
        if new_individual1[-1] != individual1_rep[-1]:
            new_individual1.append(individual1_rep[-1])
        if new_individual2[-1] != individual2_rep[-1]:
            new_individual2.append(individual2_rep[-1])
        return (GASliceSolutionRepresentation(new_individual1[0], new_individual1[1], new_individual1[2], individual1.get_max_cores_per_chip(), individual1.get_max_chips()),
                GASliceSolutionRepresentation(new_individual2[0], new_individual2[1], new_individual2[2], individual2.get_max_cores_per_chip(), individual2.get_max_chips()),
                )

        


    def get_k(self):
        return self._k

    def __str__(self):
        return "slice_uniform"
    
