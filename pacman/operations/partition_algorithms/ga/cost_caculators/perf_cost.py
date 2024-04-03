from typing import List, Tuple
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_representations.slice_representation import GASliceSolutionRepresentation
from pacman.operations.partition_algorithms.ga.cost_caculators.abst_cost_calculator import AbstractGaCostCalculator
from spinn_utilities.overrides import overrides
from pacman.operations.partition_algorithms.neurodynamics.ising_model import IsingModel2D
from numpy.typing import NDArray
import numpy as np
import random

class ProfilingSamplingBasedIsingModelCost(AbstractGaCostCalculator):
    @overrides(AbstractGaCostCalculator._calculate_cost_for_single_individual)
    def _calculate_cost_for_single_individual(self, solution: AbstractGASolutionRepresentation) -> List[float]:
        if not isinstance(solution, GASliceSolutionRepresentation):
            raise NotImplemented
        
        ptype_solution_representation: List[int] = solution.get_ptype_solution_representation()
        sampling_count = len(self._samples)
        accumulated_cost = 0.0

        def find_chip_core(neuron_index) -> Tuple[int, int]:
            # binary search
            left = 0
            right = len(ptype_solution_representation) - 1
            while left <= right:
                mid = (right - left) // 2 + left
                current_target_slice = ptype_solution_representation[mid]
                current_target_slice_neuron_index_from = current_target_slice[GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX]
                current_target_slice_neuron_index_to = current_target_slice[GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX]
                if neuron_index >= current_target_slice_neuron_index_from and neuron_index <= current_target_slice_neuron_index_to:
                    return (current_target_slice[GASliceSolutionRepresentation.CHIP_INDEX], current_target_slice[GASliceSolutionRepresentation.CORE_INDEX])
                if neuron_index < current_target_slice_neuron_index_from:
                    right = mid - 1
                    continue
                if neuron_index > current_target_slice_neuron_index_to:
                    left = mid + 1
                    continue
            raise ValueError

        def calculate_single_cost(sample: bytearray):
            # For all neuron pairs, caculates the cost of this pairs.
            # 1. no neuron in the pair are activated --> 0
            # 2. one of the neuron in the pair is activated -> 0
            # 3. both of the neuron in the pair are activated -> 
            ### 3.1 on the same core ->
            ### 3.2 on the same chip ->
            ### 3.3 on different chip.
            N = len(sample)
            cost = 0.0
            for i in range(0, N):
                for j in range(0, i):
                    if sample[i] == -1 and sample[j] == -1:
                        cost += self._cost_no_activation
                        continue
                    
                    if (sample[i] == 1 and sample[j] == -1) or (sample[i] == -1 and sample[j] == 1):
                        cost += self._cost_one_activation
                        continue

                    neuron_i_chip_id, neuron_i_core_id = find_chip_core(i)
                    neuron_j_chip_id, neuron_j_core_id = find_chip_core(j)
                    
                    if neuron_i_chip_id == neuron_j_chip_id and neuron_i_core_id == neuron_j_core_id:
                        cost += self._cost_same_core
                        continue
                    
                    if neuron_i_chip_id == neuron_i_core_id:
                        cost += self._cost_differnt_core_same_chip
                        continue
                    
                    cost += self._cost_different_chip
            return cost

        # Sampling neuron network states.
        # Calculate the average cost of sampled states under the given neurons placement.
        for i in range(0, sampling_count):
            sample = self._samples[i]
            # it may better utilize $\sum_s p(s)cost(s)$. It require the partition function Z, when calculate p(s).
            single_cost = calculate_single_cost(sample)
            accumulated_cost += single_cost
        accumulated_cost /= sampling_count
        return accumulated_cost
    
    def __init__(self, ising_model: IsingModel2D, samples,
        cost_no_activation=0.0, cost_one_activation=1.0, cost_same_core=2.0,\
        cost_differnt_core_same_chip=3.0, cost_different_chip=4.0) -> None:
            super().__init__()
            if len(ising_model.get_H().shape) != 1 or len(ising_model.get_J().shape) != 2 or ising_model.get_J().shape[0] != ising_model.get_J().shape[1] or ising_model.get_H().shape[0] != ising_model.get_J().shape[1]:
                raise ValueError
            self._ising_model = ising_model
            self._samples = samples
            self._cost_no_activation = cost_no_activation
            self._cost_one_activation = cost_one_activation
            self._cost_same_core = cost_same_core
            self._cost_differnt_core_same_chip = cost_differnt_core_same_chip
            self._cost_different_chip = cost_different_chip
            
    def __str__(self):
        return "perf_cost_ising"
