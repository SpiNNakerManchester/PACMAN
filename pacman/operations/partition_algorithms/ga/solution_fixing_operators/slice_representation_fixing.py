from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_fixing_operators.abst_solution_fixing import AbstractGaSolutionFixing
from pacman.operations.partition_algorithms.ga.solution_representations.slice_representation import GASliceSolutionRepresentation
from typing import Tuple, List
from spinn_utilities.overrides import overrides
from pacman.operations.partition_algorithms.ga.entities.resource_conf import ResourceConfiguration
import pandas as pd


class GaSliceRepresenationSolutionSimpleFillingFixing(AbstractGaSolutionFixing):
    @overrides(AbstractGaSolutionFixing.do_solution_fixing)
    def _do_solution_fixing(self, solution: AbstractGASolutionRepresentation) -> AbstractGASolutionRepresentation:
        if not isinstance(solution, GASliceSolutionRepresentation):
            raise TypeError
        if solution._use_ptype:
            self._fixing_in_ptype_representation(solution)
        else:
            self._fixing_in_gtype_representation(solution)

    def _fixing_in_ptype_representation(self, solution: AbstractGASolutionRepresentation):
        ptype_representation: List[Tuple] = solution.get_ptype_solution_representation() 

        # Ensure slice's ending >= slice's beginning
        for i in range(0, len(ptype_representation)):
            if ptype_representation[i][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX] < ptype_representation[i][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX]:
                t = ptype_representation[i][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX]
                ptype_representation[i][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX] = ptype_representation[i][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX]
                ptype_representation[i][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX] = t

        # Sort by each slice's beginning
        ptype_representation.sort(key = lambda slice_info: slice_info[GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX])
        ptype_representation_length = len(ptype_representation)
        new_ptype_representation = []
        pt = 1
        last_slice_neuron_index_from = ptype_representation[0][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX]
        last_slice_neuron_index_to = ptype_representation[0][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX]
        new_ptype_representation.append(ptype_representation[0])

        while pt < ptype_representation_length:
            slice_neuron_index_from = ptype_representation[pt][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX]
            slice_neuron_index_to = ptype_representation[pt][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX]
            if slice_neuron_index_from < 0:
                continue
            if slice_neuron_index_from >= self.res_configuration.get_neruon_count() or slice_neuron_index_to >= self.res_configuration.get_neruon_count():
                break
            if slice_neuron_index_from == last_slice_neuron_index_to + 1:
                # No need any processing.
                new_ptype_representation.append(ptype_representation[pt])
                last_slice_neuron_index_from = ptype_representation[pt]
                last_slice_neuron_index_to = ptype_representation[pt]
                pt += 1
                continue

            if slice_neuron_index_from > last_slice_neuron_index_to + 1:
                # Fill vacancy. (Chip index and core index's decision are pending.)
                new_ptype_representation.append((last_slice_neuron_index_to + 1, slice_neuron_index_from - 1, -1, -1))
                last_slice_neuron_index_from = last_slice_neuron_index_to + 1
                last_slice_neuron_index_to = slice_neuron_index_from - 1
                continue

            if slice_neuron_index_from < last_slice_neuron_index_to + 1:
                # when current slice is totally overlapped by the previous one, ignore current slice.
                if slice_neuron_index_to <= last_slice_neuron_index_to:
                    continue

                new_previous_slice_to = (last_slice_neuron_index_to + slice_neuron_index_from) // 2
                new_current_slice_from = new_previous_slice_to + 1
            
                new_ptype_representation[-1][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX]\
                      = new_previous_slice_to
                ptype_representation[pt][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX] = new_current_slice_from
                new_ptype_representation.append((new_current_slice_from + 1, slice_neuron_index_to, -1, -1))
                last_slice_neuron_index_from = new_current_slice_from
                last_slice_neuron_index_to = slice_neuron_index_to
                pt += 1
                continue
        
        # Fill Vacancy of the beginning part and the ending part
        if new_ptype_representation[0][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX] > 0:
            new_ptype_representation.insert(0, (0, new_ptype_representation[0][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX - 1], -1, -1))
        if new_ptype_representation[-1][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX] < self.res_configuration.get_neruon_count() - 1:
            new_ptype_representation.append((new_ptype_representation[-1][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX] + 1, self.res_configuration.get_neruon_count() - 1, -1, -1))
        
        self.__fixing_chip_core_in_ptype(new_ptype_representation)
    
    def __fixing_chip_core_in_ptype(self, ptype_solution):
        SLCIE_NEURON_FROM_INDEX = GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX
        SLCIE_NEURON_TO_INDEX = GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX
        CHIP_INDEX = GASliceSolutionRepresentation.CHIP_INDEX
        CORE_INDEX = GASliceSolutionRepresentation.CORE_INDEX

        slice_count = len([ptype_solution])
        # Ensure the use of cores and chips satisfies resource limiatation described by 
        # 'max_chips' and 'max_cores_per_chip' 
        
        # 1. Make all illegal core index and chip index be -1
        slices_data_frame = pd.DataFrame(ptype_solution, columns = ["slice_neuron_index_from", "slice_neuron_index_to", "chip_id", "core_id"])
        slices_data_frame[slices_data_frame["core_id"] < 0] = -1
        slices_data_frame[slices_data_frame["core_id"] > self.res_configuration.get_max_cores_per_chip()] = -1
        slices_data_frame[slices_data_frame["chip_id"] < 0] = -1
        slices_data_frame[slices_data_frame["chip_id"] > self.res_configuration.get_max_chips()] = -1


        # 2. Make all slice's size can be fitted in a core.


        # 3. Make lookup table for searching slices by using (core_index, chip_index) pair.
            # Slices are represented by DataFrame.
            # DataFrames are sort by chip_index and core_index.

            # grouped_result: List[List[chip_core_identification: int, List[core_index, slice_infos: DataFrame]]]
        
        chip_core_records = \
            [
                [
                    chip_index,
                    [
                        [core_index, chip_core_df] \
                        for core_index, chip_core_df \
                        in chip_df.groupby(lambda item: item[CORE_INDEX])
                    ]
                ].sort(key=lambda x: x[0])
                    for chip_index, chip_df
                    in slices_data_frame.groupby(lambda item: item[CHIP_INDEX])
            ].sort(key=lambda x: x[0])

        # Create a map that map (chip_index, core_index) to (space usage)
        for slice_index in range(0, slice_count):
            if slice_count[slice_index][GASliceSolutionRepresentation.CHIP_INDEX] != -1 and \
                slice_count[slice_index][GASliceSolutionRepresentation.CORE_INDEX] != -1:
                # Unnecessary be processed.
                continue
            # 1. Find whether the slice 

    def __init__(self, resource_configuration: ResourceConfiguration) -> None:
        super().__init__()
        self.res_configuration = resource_configuration

    def _fixing_in_gtype_representation(self, solution: AbstractGASolutionRepresentation):
        raise NotImplementedError
    
    def __str__(self):
        return "slice_rep_fixing"