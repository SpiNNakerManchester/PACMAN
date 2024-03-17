from pacman.operations.partition_algorithms.ga.crossover_individuals_selectors.abst_crossover_individuals_selector import AbstractGaCrossoverIndividualSelector
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.cost_caculators.abst_cost_calculator import AbstractGaCostCalculator
from typing import List, Tuple
from spinn_utilities.overrides import overrides
import random
import numpy as np
class MinMaxNormalizationWeightInvidualSelection(AbstractGaCrossoverIndividualSelector):
    @overrides(AbstractGaCrossoverIndividualSelector._do_select_individuals)
    def _do_select_individuals(self, solutions: List[AbstractGASolutionRepresentation], costs: List[int]) -> List[AbstractGASolutionRepresentation]:
        select_indexes = []
        indexes = range(0, len(solutions))
        weights = self._generate_selection_weights(costs)
        while len(select_indexes) < 2:
            random_index = random.choices(indexes, weights, k=1)[0]
            if random_index not in select_indexes:
                select_indexes.append(random_index)
        selected_individuals = [solutions[index] for index in select_indexes[:2]]
        return selected_individuals[0], selected_individuals[1]
    
    def _generate_selection_weights(self, costs):
        # currently, use min_max normalization to generate random selection weights.
        # performance maybe improved by using gaussian heatmap.
        if max(costs) == min(costs):
            return [1.0 / (len(costs))] * len(costs)
        return (np.array(costs) - min(costs)) / (max(costs) - min(costs))
    
    def __str__(self):
        return "minmax_random_ind_sel"

class GaussianWeightInvidualSelection(AbstractGaCrossoverIndividualSelector):
    @overrides(AbstractGaCrossoverIndividualSelector._do_select_individuals)
    def _do_select_individuals(self, solutions: List[AbstractGASolutionRepresentation], costs: List[int]) ->  Tuple[AbstractGASolutionRepresentation, AbstractGASolutionRepresentation]:
        select_indexes = []
        indexes = range(0, len(solutions))
        weights = self._generate_selection_weights(costs)
        while len(select_indexes) < 2:
            random_index = random.choices(population=indexes, weights=weights, k=1)[0]
            if random_index not in select_indexes:
                select_indexes.append(random_index)
            selected_individuals = [solutions[index] for index in select_indexes[:2]]
        return selected_individuals[0], selected_individuals[1]
    
    def _generate_selection_weights(self, costs):
        if(len(costs) <= 1):
            return costs
        mu = np.average(costs)
        s = np.sqrt(np.sum((np.array(costs) - mu) ** 2)) / (len(costs) - 1)
        return ([1.0 / (len(costs))] * len(costs)) if s == 0 else (costs - mu) / s

    def __str__(self):
        return "nor_gaussian_random_ind_sel"