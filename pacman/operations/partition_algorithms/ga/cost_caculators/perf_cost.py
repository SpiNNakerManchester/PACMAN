from typing import List
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_representations.slice_representation import GASliceSolutionRepresentation

from pacman.operations.partition_algorithms.ga.cost_caculators.abst_cost_calculator import AbstractGaCostCalculator
from spinn_utilities.overrides import overrides
from numpy.typing import NDArray
import numpy as np
import random
class ProfilingIsingModelCost(AbstractGaCostCalculator):

    @override(AbstractGaCostCalculator._calculate_cost_for_single_individual)
    def _calculate_cost_for_single_individual(self, solution: AbstractGASolutionRepresentation) -> List[float]:
        common_solution_representation = solution.to_common_representation()
        ptype_solution_representation: List[int] = common_solution_representation.get_ptype_solution_representation()
        sampling_count = len(ptype_solution_representation) if self._sampling_count <= 0 else self._sampling_count
        cost = 0.0
        

        def find_chip_core(neuron_index):
            # binary search
            left = 0
            right = len(ptype_solution_representation)
            while left <= right:
                mid = (right - left) // 2 + left
                current_target_slice = ptype_solution_representation[mid]
                current_target_slice_neuron_index_from = current_target_slice[GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX]
                current_target_slice_neuron_index_to = current_target_slice[GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX]
                if neuron_index >= current_target_slice_neuron_index_from and neuron_index <= current_target_slice_neuron_index_to:
                    return mid
                if neuron_index < current_target_slice_neuron_index_from:
                    right = mid - 1
                    continue
                if neuron_index > current_target_slice_neuron_index_to:
                    left = mid + 1
                    continue
            raise ValueError

        def calculate_single_cost(sample: bytearray, ptype_solution_representation, Z):
            hamiltonian = calculate_hamiltonian(sample)
            # # For calculate cost, the normalization factor in calculating graph state possibility.
            # # The is not be considered currently.
            # # The cost of different.
            normalization_factor = Z
            p = np.exp(-hamiltonian) / normalization_factor
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
                    if sample[i] == '0' and sample[j] == '0':
                        cost += self._cost_no_activation
                        continue
                    if (sample[i] == '1' and sample[j] == '0') or (sample[i] == '0' and sample[j] == '1'):
                        cost += self._cost_one_activation
                        continue
                    chip_core_index_i = find_chip_core(i)
                    chip_core_index_j = find_chip_core(j)
                    if chip_core_index_i[0] == chip_core_index_i[0] and chip_core_index_i[1] == chip_core_index_i[1]:
                        cost += self._cost_same_core
                        continue
                    if chip_core_index_i[0] == chip_core_index_i[0]:
                        cost += self._cost_differnt_core_same_chip
                        continue
                    cost += self._cost_different_chip

            return p * cost


        def sampling_one(neuron_count) -> bytearray:
            sample = bytearray(neuron_count)
            for i in range(0, neuron_count):
                sample[i] = '1' if random.random() < self._J[i] else '0'
            return sample

        def calculate_Z(N):
            z = 2
            Z = np.exp(-self._beta * self._J * z * self._mean_field ** 2 * N / 2) * \
                (2 * np.cosh(self._beta * (self._J * z * self._mean_field + self._H))) ** N
            return Z

        def calculate_hamiltonian(sample: bytearray) -> bytearray:
            hamiltonian  = 0.0
            interaction_factor = 0.0
            activation_factor = 0.0
            # Activation factor
            for j in range(0, len(ptype_solution_representation)):
                h_j = self._H[j]
                sigma_j = 1 if sample[j] == '1' else -1
                activation_factor += h_j * sigma_j
            activation_factor *= self._mean_field
            hamiltonian = -activation_factor

            for i in range(0, len(ptype_solution_representation)):
                for j in range(0, i):
                    h_j = self._H[j]
                    sigma_i = 1 if sample[i] == '1' else -1
                    sigma_j = 1 if sample[j] == '1' else -1

                    interaction_factor += sigma_i * sigma_j * self._J[i, j]
            activation_factor *= self._mean_field
            hamiltonian = - interaction_factor - activation_factor


            return hamiltonian

        # Sampling neuron network states.
        # Calculate the average cost of sampled states under the given neurons placement.
        Z = calculate_Z()
        for _ in range(0, sampling_count):
            sample = sampling_one(len(ptype_solution_representation))
            
            single_cost = calculate_single_cost(sample, ptype_solution_representation, Z)
            cost += single_cost
        cost /= sampling_count
        return cost
    def __init__(self, H: NDArray, J: NDArray, mean_field, \
                 normalization_factor = np.inf, sampling_count = -1, beta = 1.0,\
                    cost_no_activation=0.0, cost_one_activation=1.0, cost_same_core=2.0,\
                    cost_differnt_core_same_chip=3.0, cost_different_chip=4.0) -> None:
        super().__init__()
        if len(H.shape) or len(J.shape) != 2 or J.shape[0] != J.shape[1] or H.shape[0] != J.shape[1]:
            raise ValueError
        self._H = H
        self._J = J
        self._mean_field = mean_field
        self._sampling_count = sampling_count
        self._normalization_factor = normalization_factor
        self._beta = 1.0
        self._cost_no_activation = cost_no_activation
        self._cost_one_activation = cost_no_activation
        self._cost_same_core = cost_same_core
        self._cost_differnt_core_same_chip = cost_differnt_core_same_chip
        self._cost_different_chip = cost_different_chip



        
    def __str__(self):
        return "c1_cost"