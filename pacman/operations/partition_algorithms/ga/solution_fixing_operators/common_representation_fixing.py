from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_fixing_operators.abst_solution_fixing import AbstractGaSolutionFixing
from pacman.operations.partition_algorithms.ga.solution_representations.slice_representation import GASliceSolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_representations.common_ga_solution_representation import CommonGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_fixing_operators.slice_representation_fixing import GaSliceRepresenationSolutionSimpleFillingFixing

from typing import Tuple, List
from spinn_utilities.overrides import overrides
from pacman.operations.partition_algorithms.ga.entities.resource_configuration import ResourceConfiguration
import pandas as pd
from pacman.operations.partition_algorithms.solution_adopter import SolutionAdopter
from pacman.model.graphs.application import ApplicationGraph
from pacman.operations.partition_algorithms.utils.sdram_calculator import SDRAMCalculator


class CommonGARepresenationSolutionSimpleFillingFixing(AbstractGaSolutionFixing):
    @overrides(AbstractGaSolutionFixing._do_solution_fixing)
    def _do_solution_fixing(self, solution: AbstractGASolutionRepresentation) -> AbstractGASolutionRepresentation:
        if not isinstance(solution, CommonGASolutionRepresentation):
            raise TypeError
        if solution._use_ptype:
            return self._fixing_in_ptype_representation(solution)
        else:
            return self._fixing_in_gtype_representation(solution)

    def _fixing_in_ptype_representation(self, solution: AbstractGASolutionRepresentation):
        slice_representation_solution: GASliceSolutionRepresentation = \
            GASliceSolutionRepresentation()
        slice_representation_solution = slice_representation_solution.from_common_representation(solution)

        slice_fixing = GaSliceRepresenationSolutionSimpleFillingFixing(self.res_configuration, self._application_graph)
        slice_representation_solution = slice_fixing.do_solution_fixing(slice_representation_solution)
        comm_solution = slice_representation_solution.to_common_representation()
        solution.set_new_representation_solution(comm_solution)
        return solution

    def __init__(self, resource_configuration: ResourceConfiguration, application_graph: ApplicationGraph) -> None:
        super().__init__()
        self._resource_constraint_configuration = resource_configuration
        self._application_graph = application_graph
        # calculate max_slice_length
        self._max_slice_length = self._calculate_max_slice_lengths()

    def _calculate_max_slice_lengths(self) -> List[int]:
        return [SDRAMCalculator(application_vertex).calculate_max_slice_length(application_vertex, self._resource_constraint_configuration.get_neruon_count(), self._resource_constraint_configuration.get_max_sdram()) for application_vertex in self._application_graph.vertices]


    def _fixing_in_gtype_representation(self, solution: AbstractGASolutionRepresentation):
        raise NotImplementedError
    
    def __str__(self):
        return "slice_rep_fixing"