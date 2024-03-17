from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.crossover_operators.abst_crossover import AbstractGaCrossover
from pacman.operations.partition_algorithms.ga.solution_representations.common_ga_solution_representation import CommonGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_representations.slice_representation import GASliceSolutionRepresentation

from spinn_utilities.overrides import overrides
from typing import Tuple
import random
import numpy as np

class GaSliceCrossoverKPoints(AbstractGaCrossover):
    SLICE_RECORD_NEURON_TO_INDEX = GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX
    SLICE_RECORD_CHIP_INDEX = GASliceSolutionRepresentation.CHIP_INDEX
    SLICE_RECORD_CORE_INDEX = GASliceSolutionRepresentation.CORE_INDEX
    
    def __init__(self, k:int, use_ptype=True) -> None:
        super().__init__()
        self._k = k
        self._use_ptype = use_ptype

    @overrides(AbstractGaCrossover._do_crossover)
    def _do_crossover(self, individual1: GASliceSolutionRepresentation, individual2: GASliceSolutionRepresentation) -> Tuple[AbstractGaCrossover, AbstractGaCrossover]:
        if not isinstance(individual1, GASliceSolutionRepresentation) or not isinstance(individual2, GASliceSolutionRepresentation):
            raise TypeError
        
        # crossover base on ptype
        individual1_rep = individual1.get_ptype_solution_representation()
        individual2_rep = individual2.get_ptype_solution_representation()
        
        # last element should be neuron_count - 1. Two solutions should cover the same count of neurons.
        if(individual1_rep[-1][self.SLICE_RECORD_NEURON_TO_INDEX] != individual2_rep[-1][self.SLICE_RECORD_NEURON_TO_INDEX]):
            raise ValueError
        
        sorted_combination_slice_info = \
            sorted(\
                [[slice_record[self.SLICE_RECORD_NEURON_TO_INDEX], slice_record[self.SLICE_RECORD_CHIP_INDEX], slice_record[self.SLICE_RECORD_CORE_INDEX]] \
                    for slice_record in individual1_rep] + \
            [[slice_record[self.SLICE_RECORD_NEURON_TO_INDEX], slice_record[self.SLICE_RECORD_CHIP_INDEX], slice_record[self.SLICE_RECORD_CORE_INDEX]] \
                    for slice_record in individual2_rep])
        
        new_individual1 = [[], [], []]
        new_individual2 = [[], [], []]
        new_individuals = [new_individual1, new_individual2]

        # select k indexes from [0, len(sorted_combination_slice_info))
        k_point_indexes = sorted(random.sample(range(0, len(sorted_combination_slice_info)), k=self.get_k()))
        last_point_index = -1
        for point_index in k_point_indexes:
            index_individual_place_slice_endpoint = random.choices([0, 1], k = 1)[0]

            # (last_point_index + 1)-th ~ point_index-th slices in the combined slice list are prepared to be placed into new_individuals[index_individual_place_slice_endpoint]
            for i in range(last_point_index + 1, point_index + 1):
                # ensure that two slices with the same NEURON_TO_INDEX not be placed into a single individual.
                if len(new_individuals[index_individual_place_slice_endpoint][0]) != 0 and \
                    sorted_combination_slice_info[i][0] == new_individuals[index_individual_place_slice_endpoint][0][-1]:
                    index_individual_place_slice_endpoint = 1 - index_individual_place_slice_endpoint
                
                new_individuals[index_individual_place_slice_endpoint][0].append(sorted_combination_slice_info[i][0])
                new_individuals[index_individual_place_slice_endpoint][1].append(sorted_combination_slice_info[i][1])
                new_individuals[index_individual_place_slice_endpoint][2].append(sorted_combination_slice_info[i][2])
            last_point_index = point_index

        if new_individual1[0][-1] != individual1_rep[-1][self.SLICE_RECORD_NEURON_TO_INDEX]:
            new_individual1[0].append(individual1_rep[-1][self.SLICE_RECORD_NEURON_TO_INDEX])
            new_individual1[1].append(individual1_rep[-1][self.SLICE_RECORD_CHIP_INDEX])
            new_individual1[2].append(individual1_rep[-1][self.SLICE_RECORD_CORE_INDEX])

        if new_individual2[0][-1] != individual2_rep[-1][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX]:
            new_individual2[0].append(individual2_rep[-1][self.SLICE_RECORD_NEURON_TO_INDEX])
            new_individual2[1].append(individual2_rep[-1][self.SLICE_RECORD_CHIP_INDEX])
            new_individual2[2].append(individual2_rep[-1][self.SLICE_RECORD_CORE_INDEX])

        return (GASliceSolutionRepresentation(new_individual1[0], new_individual1[1], new_individual1[2], individual1.get_max_cores_per_chip(), individual1.get_max_chips(), True),
                GASliceSolutionRepresentation(new_individual2[0], new_individual2[1], new_individual2[2], individual2.get_max_cores_per_chip(), individual2.get_max_chips(), True))

    def get_k(self):
        return self._k

    def __str__(self):
        return "slice_k_points_cv"

# unused
class GaSliceCrossoverUniform(AbstractGaCrossover):
    SLICE_RECORD_NEURON_TO_INDEX = GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX
    SLICE_RECORD_CHIP_INDEX = GASliceSolutionRepresentation.CHIP_INDEX
    SLICE_RECORD_CORE_INDEX = GASliceSolutionRepresentation.CORE_INDEX
    
    def __init__(self, use_ptype=False) -> None:
        super().__init__()
        self._use_ptype = use_ptype

    @overrides(AbstractGaCrossover._do_crossover)
    def _do_crossover(self, individual1: AbstractGASolutionRepresentation, individual2: AbstractGASolutionRepresentation) -> Tuple[AbstractGaCrossover, AbstractGaCrossover]:
        if not isinstance(individual1, GASliceSolutionRepresentation) or not isinstance(individual2, GASliceSolutionRepresentation):
            raise TypeError
        individual1_rep = individual1.get_ptype_solution_representation()
        individual2_rep = individual2.get_ptype_solution_representation()
        # last element should be neuron_count - 1. Two solutions should cover the same count of neurons.
        if(individual1_rep[-1] != individual2_rep[-1]):
            raise ValueError
        individual1_length = len(individual1_rep)
        individual2_length = len(individual2_rep)
        individuals = [individual1_rep, individual2_rep]
        P = [0, 0]
        new_individual1 = [[], [], []]
        new_individual2 = [[], [], []]
        while P[0] < individual1_length and P[1] < individual2_length:
            select_individual = random.choices([0, 1], k = 1)[0]
            
            new_individual1[0].append(individuals[select_individual][P[select_individual]][self.SLICE_RECORD_NEURON_TO_INDEX])
            new_individual1[1].append(individuals[select_individual][P[select_individual]][self.SLICE_RECORD_CHIP_INDEX])
            new_individual1[2].append(individuals[select_individual][P[select_individual]][self.SLICE_RECORD_CORE_INDEX])

            P[select_individual] += 1
            while individuals[1 - select_individual][P[1 - select_individual]] < individuals[select_individual][P[select_individual]]:
                new_individual2[0].append(individuals[1 - select_individual][P[1 - select_individual]][self.SLICE_RECORD_NEURON_TO_INDEX])
                new_individual2[1].append(individuals[1 - select_individual][P[1 - select_individual]][self.SLICE_RECORD_CHIP_INDEX])
                new_individual2[2].append(individuals[1 - select_individual][P[1 - select_individual]][self.SLICE_RECORD_CORE_INDEX])
                P[1 - select_individual] += 1
        if new_individual1[-1] != individual1_rep[-1]:
            new_individual1.append(individual1_rep[-1])
        if new_individual2[-1] != individual2_rep[-1]:
            new_individual2.append(individual2_rep[-1])
        return (GASliceSolutionRepresentation(new_individual1[0], new_individual1[1], new_individual1[2], individual1.get_max_cores_per_chip(), individual1.get_max_chips()),
                GASliceSolutionRepresentation(new_individual2[0], new_individual2[1], new_individual2[2], individual2.get_max_cores_per_chip(), individual2.get_max_chips()))

    def __str__(self):
        return "slice_uniform_crossover"
    


class GaSliceSliceInfoCombinationUniformCrossover(AbstractGaCrossover):
    SLICE_RECORD_NEURON_TO_INDEX = GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX
    SLICE_RECORD_CHIP_INDEX = GASliceSolutionRepresentation.CHIP_INDEX
    SLICE_RECORD_CORE_INDEX = GASliceSolutionRepresentation.CORE_INDEX
    
    def __init__(self, use_ptype=False) -> None:
        super().__init__()
        self._use_ptype = use_ptype
    
    @overrides(AbstractGaCrossover._do_crossover)
    def _do_crossover(self, individual1: AbstractGASolutionRepresentation, individual2: AbstractGASolutionRepresentation) -> Tuple[AbstractGaCrossover, AbstractGaCrossover]:
        if not isinstance(individual1, GASliceSolutionRepresentation) or not isinstance(individual2, GASliceSolutionRepresentation):
            raise TypeError
        individual1_rep = individual1.get_ptype_solution_representation()
        individual2_rep = individual2.get_ptype_solution_representation()
        # last element should be neuron_count - 1. Two solutions should cover the same count of neurons.
        if(individual1_rep[-1][self.SLICE_RECORD_NEURON_TO_INDEX] != individual2_rep[-1][self.SLICE_RECORD_NEURON_TO_INDEX]):
            raise ValueError
        
        sorted_combination_slice_info = \
            sorted(\
                [[slice_record[self.SLICE_RECORD_NEURON_TO_INDEX], slice_record[self.SLICE_RECORD_CHIP_INDEX], slice_record[self.SLICE_RECORD_CORE_INDEX]] \
                    for slice_record in individual1_rep] + \
            [[slice_record[self.SLICE_RECORD_NEURON_TO_INDEX], slice_record[self.SLICE_RECORD_CHIP_INDEX], slice_record[self.SLICE_RECORD_CORE_INDEX]] \
                    for slice_record in individual2_rep])
        
        new_individual1 = [[], [], []]
        new_individual2 = [[], [], []]
        new_individuals = [new_individual1, new_individual2]
        endpoint_index = 0
        for endpoint_index in range(0, len(sorted_combination_slice_info)):
            index_individual_place_slice_endpoint = random.choices([0, 1], k = 1)[0]
            if len(new_individuals[index_individual_place_slice_endpoint][0]) != 0 and \
                sorted_combination_slice_info[endpoint_index][0] == new_individuals[index_individual_place_slice_endpoint][0][-1]:
                index_individual_place_slice_endpoint = 1 - index_individual_place_slice_endpoint
            
            new_individuals[index_individual_place_slice_endpoint][0].append(sorted_combination_slice_info[endpoint_index][0])
            new_individuals[index_individual_place_slice_endpoint][1].append(sorted_combination_slice_info[endpoint_index][1])
            new_individuals[index_individual_place_slice_endpoint][2].append(sorted_combination_slice_info[endpoint_index][2])

        if new_individual1[0][-1] != individual1_rep[-1][self.SLICE_RECORD_NEURON_TO_INDEX]:
            new_individual1[0].append(individual1_rep[-1][self.SLICE_RECORD_NEURON_TO_INDEX])
            new_individual1[1].append(individual1_rep[-1][self.SLICE_RECORD_CHIP_INDEX])
            new_individual1[2].append(individual1_rep[-1][self.SLICE_RECORD_CORE_INDEX])

        if new_individual2[0][-1] != individual2_rep[-1][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX]:
            new_individual2[0].append(individual2_rep[-1][self.SLICE_RECORD_NEURON_TO_INDEX])
            new_individual2[1].append(individual2_rep[-1][self.SLICE_RECORD_CHIP_INDEX])
            new_individual2[2].append(individual2_rep[-1][self.SLICE_RECORD_CORE_INDEX])
        return (GASliceSolutionRepresentation(new_individual1[0], new_individual1[1], new_individual1[2], individual1.get_max_cores_per_chip(), individual1.get_max_chips(), True),
                GASliceSolutionRepresentation(new_individual2[0], new_individual2[1], new_individual2[2], individual2.get_max_cores_per_chip(), individual2.get_max_chips(), True))

    def __str__(self):
        return "slice_comb_uni_cv"
    
