from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.crossover_operators.abst_crossover import AbstractGaCrossover
from pacman.operations.partition_algorithms.ga.solution_representations.common_ga_solution_representation import CommonGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_representations.slice_representation import GASliceSolutionRepresentation

from spinn_utilities.overrides import overrides
from typing import Tuple
import random
import numpy as np


class GaSliceCrossoverKPoints(AbstractGaCrossover):
    def __init__(self, k: int, use_ptype=False) -> None:
        super().__init__()
        self._k = k
        self._use_ptype = use_ptype

    @overrides(AbstractGaCrossover._do_crossover)
    def _do_crossover(self, individual1: GASliceSolutionRepresentation, individual2: GASliceSolutionRepresentation) -> Tuple[AbstractGaCrossover, AbstractGaCrossover]:
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
        SLICE_RECORD_TO_INDEX = individual1.SLICE_NEURON_TO_INDEX
        SLICE_RECORD_CHIP_INDEX = individual1.CHIP_INDEX
        SLICE_RECORD_CORE_INDEX = individual1.CORE_INDEX
        while P[0] < individual1_length and P[1] < individual2_length:
            select_individual = random.choices([0, 1], k = 1)[0]    
            new_individual1[0].append(individuals[select_individual][P[select_individual]][SLICE_RECORD_TO_INDEX])
            new_individual1[1].append(individuals[select_individual][P[select_individual]][SLICE_RECORD_CHIP_INDEX])
            new_individual1[2].append(individuals[select_individual][P[select_individual]][SLICE_RECORD_CORE_INDEX])

            P[select_individual] += 1
            while individuals[1 - select_individual][P[1 - select_individual]] < individuals[select_individual][P[select_individual]]:
                new_individual2[0].append(individuals[1 - select_individual][P[1 - select_individual]][SLICE_RECORD_TO_INDEX])
                new_individual2[1].append(individuals[1 - select_individual][P[1 - select_individual]][SLICE_RECORD_CHIP_INDEX])
                new_individual2[2].append(individuals[1 - select_individual][P[1 - select_individual]][SLICE_RECORD_CORE_INDEX])
                P[1 - select_individual] += 1
        
        if new_individual1[-1] != individual1_rep[-1]:
            new_individual1.append(individual1_rep[-1])
        if new_individual2[-1] != individual2_rep[-1]:
            new_individual2.append(individual2_rep[-1])
        return (GASliceSolutionRepresentation(new_individual1[0], new_individual1[1], new_individual1[2], individual1.get_max_cores_per_chip(), individual1.get_max_chips()),
                GASliceSolutionRepresentation(new_individual2[0], new_individual2[1], new_individual2[2], individual2.get_max_cores_per_chip(), individual2.get_max_chips()))

    def get_k(self):
        return self._k

    def __str__(self):
        return "slice_uniform_crossover"

class GaSliceCrossoverUniform(AbstractGaCrossover):
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
        SLICE_RECORD_TO_INDEX = individual1.SLICE_NEURON_TO_INDEX
        SLICE_RECORD_CHIP_INDEX = individual1.CHIP_INDEX
        SLICE_RECORD_CORE_INDEX = individual1.CORE_INDEX
        while P[0] < individual1_length and P[1] < individual2_length:
            select_individual = random.choices([0, 1], k = 1)[0]
            
            new_individual1[0].append(individuals[select_individual][P[select_individual]][SLICE_RECORD_TO_INDEX])
            new_individual1[1].append(individuals[select_individual][P[select_individual]][SLICE_RECORD_CHIP_INDEX])
            new_individual1[2].append(individuals[select_individual][P[select_individual]][SLICE_RECORD_CORE_INDEX])

            P[select_individual] += 1
            while individuals[1 - select_individual][P[1 - select_individual]] < individuals[select_individual][P[select_individual]]:
                new_individual2[0].append(individuals[1 - select_individual][P[1 - select_individual]][SLICE_RECORD_TO_INDEX])
                new_individual2[1].append(individuals[1 - select_individual][P[1 - select_individual]][SLICE_RECORD_CHIP_INDEX])
                new_individual2[2].append(individuals[1 - select_individual][P[1 - select_individual]][SLICE_RECORD_CORE_INDEX])
                P[1 - select_individual] += 1
        
        if new_individual1[-1] != individual1_rep[-1]:
            new_individual1.append(individual1_rep[-1])
        if new_individual2[-1] != individual2_rep[-1]:
            new_individual2.append(individual2_rep[-1])
        return (GASliceSolutionRepresentation(new_individual1[0], new_individual1[1], new_individual1[2], individual1.get_max_cores_per_chip(), individual1.get_max_chips()),
                GASliceSolutionRepresentation(new_individual2[0], new_individual2[1], new_individual2[2], individual2.get_max_cores_per_chip(), individual2.get_max_chips()))


    def __str__(self):
        return "slice_uniform"
    
