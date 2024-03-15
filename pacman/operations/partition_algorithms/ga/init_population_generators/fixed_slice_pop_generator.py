from pacman.operations.partition_algorithms.ga.init_population_generators.abst_init_pop_generator import AbstractGaInitialPopulationGenerator
from pacman.operations.partition_algorithms.ga.solution_representations.common_ga_solution_representation import CommonGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_representations.slice_representation import GASliceSolutionRepresentation
from pacman.model.graphs.application import ApplicationGraph
from typing import List
from spinn_utilities.overrides import overrides
import numpy as np

class GaFixedSlicePopulationGenerator(AbstractGaInitialPopulationGenerator):
    def __init__(self,  fixed_slice_sizes: List[int], max_cores_per_chip = 18) -> None:
        super().__init__()
        if(max_cores_per_chip < 0 or any(slice_size <= 0 for slice_size in fixed_slice_sizes)):
            raise ValueError
        self._max_core_per_chips = max_cores_per_chip
        self._fixed_slice_sizes = fixed_slice_sizes
            
    def make_solution(self, fixed_slice_size, application_graph):
        return self._make_solution(fixed_slice_size)
    
    def _make_solution(self, fixed_slice_size, application_graph):
        ag = application_graph
        neuron_count = int(np.sum([vertex.n_atoms for vertex in ag.vertices]))
        max_chips = neuron_count
        max_cores_per_chip = self._max_core_per_chips
        single_neuron_encoding_length = int(np.ceil(np.log2(max_chips * max_cores_per_chip))) * neuron_count
        
        slices_end_points = []
        slices_chip_indexes = []
        slices_core_indexes = []
        slice_index = 0
        current_chip_index = 0
        current_chip_remains_core = self._max_core_per_chips
        for neuron_index in range(0, neuron_count, fixed_slice_size):
            # calculate slice beginning and ending
            slice_neuron_from = neuron_index
            slice_neuron_to = min(slice_neuron_from + fixed_slice_size, neuron_count)
            slices_end_points.append(slice_neuron_to)
            if current_chip_remains_core <= 0:
                current_chip_index += 1 
                current_chip_remains_core = self._max_core_per_chips

            # append chip index and core index for the slice
            slices_chip_indexes.append(current_chip_index)
            slices_core_indexes.append(self._max_core_per_chips - current_chip_remains_core)
            current_chip_remains_core -= 1
            slice_index += 1

        return GASliceSolutionRepresentation(slices_end_points=slices_end_points,
                slices_chip_indexes=slices_chip_indexes, slices_core_indexes=slices_core_indexes, 
                max_cores_per_chip=max_cores_per_chip, max_chips=max_chips, 
                single_neuron_encoding_length=single_neuron_encoding_length)

    @overrides(AbstractGaInitialPopulationGenerator.generate_initial_population)
    def generate_initial_population(self, population_size: int, application_graph: ApplicationGraph) -> List[CommonGASolutionRepresentation]:
        solutions = []
        fixed_slice_sizes = self._fixed_slice_sizes
        if len(fixed_slice_sizes) == 0:
            raise ValueError
        for i in range(0, population_size):
            solutions.append(self._make_solution(fixed_slice_sizes[i % len(fixed_slice_sizes)], application_graph))
        return solutions

    def __str__(self):
        return "fix_slice_init_gen"