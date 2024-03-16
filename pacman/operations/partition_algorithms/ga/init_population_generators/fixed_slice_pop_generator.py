from pacman.operations.partition_algorithms.ga.init_population_generators.abst_init_pop_generator import AbstractGaInitialPopulationGenerator
from pacman.operations.partition_algorithms.ga.solution_representations.common_ga_solution_representation import CommonGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_representations.slice_representation import GASliceSolutionRepresentation
from pacman.operations.partition_algorithms.utils.sdram_recorder import SDRAMRecorder
from pacman.operations.partition_algorithms.utils.sdram_calculator import SDRAMCalculator
from pacman.model.graphs.application import ApplicationGraph
from typing import List
from spinn_utilities.overrides import overrides
import numpy as np

class GaFixedSlicePopulationPTypeGeneratorOneSliceOneCore(AbstractGaInitialPopulationGenerator):
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
        if len(ag.vertices) == 0:
            return None
        
        # 1. Calculate prefix sum of application vertexes' neuron counts
        #    this prefix sum will help the splitting process in identifiying which application vertex a slice is belongs to. 
        vertices = list(ag.vertices)
        total_neuron_count = int(np.sum([vertex.n_atoms for vertex in vertices]))
        neuron_count_prefix_sum = [0] * len(vertices)
        neuron_count_prefix_sum = vertices[0]
        for i in range(1, len(vertices)):
             neuron_count_prefix_sum[i] = neuron_count_prefix_sum[i - 1] + vertices[i].n_atoms

    
        max_chips = total_neuron_count
        max_cores_per_chip = self._max_core_per_chips
        
        slices_end_points = []
        slices_chip_indexes = []
        slices_core_indexes = []
        slice_index = 0
        current_chip_index = 0
        current_chip_remains_core = self._max_core_per_chips

        neuron_index = 0
        for application_vertex_index in range(0, len(vertices)):
            
            for inner_application_vertx_neuron_index in range(0, vertices[application_vertex_index].n_atoms, fixed_slice_size):
                # calculate slice beginning and ending. The ending cannot exceed the total neuron count - 1, 
                #   and the total count neurons from the first application vertex to current application vertex - 1 (include current application vertex).
                slice_neuron_from = neuron_index + inner_application_vertx_neuron_index
                slice_neuron_to = \
                    min(min(slice_neuron_from + fixed_slice_size, total_neuron_count - 1), neuron_count_prefix_sum[application_vertex_index] - 1)
                slices_end_points.append(slice_neuron_to)
                if current_chip_remains_core <= 0:
                    current_chip_index += 1 
                    current_chip_remains_core = self._max_core_per_chips

                # append chip index and core index for the slice
                slices_chip_indexes.append(current_chip_index)
                slices_core_indexes.append(self._max_core_per_chips - current_chip_remains_core)
                current_chip_remains_core -= 1
                slice_index += 1

        return GASliceSolutionRepresentation(data_for_build_solution=slices_end_points,
                slices_chip_indexes=slices_chip_indexes, slices_core_indexes=slices_core_indexes, 
                max_cores_per_chip=max_cores_per_chip, max_chips=max_chips, 
                use_ptype=True)

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
    
class GaFixedSlicePopulationPTypeGeneratorMultiSliceOneCore(AbstractGaInitialPopulationGenerator):
    def __init__(self,  fixed_slice_sizes: List[int], max_cores_per_chip = 18) -> None:
        super().__init__()
        if(max_cores_per_chip < 0 or any(slice_size <= 0 for slice_size in fixed_slice_sizes)):
            raise ValueError
        self._max_core_per_chips = max_cores_per_chip
        self._fixed_slice_sizes = fixed_slice_sizes
            
    def make_solution(self, fixed_slice_size, application_graph):
        return self._make_solution(fixed_slice_size)
    
    def _make_solution(self, fixed_slice_size, application_graph):
        sdram_recoder = SDRAMRecorder()
        
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

            sdram_space_required =         sdram_calculator = SDRAMCalculator()
            if current_core_sdram_remains() 
            if current_chip_remains_core <= 0:
                current_chip_index += 1 
                current_chip_remains_core = self._max_core_per_chips

            # append chip index and core index for the slice
            slices_chip_indexes.append(current_chip_index)
            slices_core_indexes.append(self._max_core_per_chips - current_chip_remains_core)
            current_chip_remains_core -= 1
            slice_index += 1

        return GASliceSolutionRepresentation(data_for_build_solution=slices_end_points,
                slices_chip_indexes=slices_chip_indexes, slices_core_indexes=slices_core_indexes, 
                max_cores_per_chip=max_cores_per_chip, max_chips=max_chips, 
                use_ptype=True)

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