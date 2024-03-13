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

class CommonGARepresenationSolutionSimpleFillingFixing(AbstractGaSolutionFixing):
    @overrides(AbstractGaSolutionFixing.do_solution_fixing)
    def _do_solution_fixing(self, solution: AbstractGASolutionRepresentation) -> AbstractGASolutionRepresentation:
        if not isinstance(solution, CommonGASolutionRepresentation):
            raise TypeError
        if solution._use_ptype:
            self._fixing_in_ptype_representation(solution)
        else:
            self._fixing_in_gtype_representation(solution)


    def _fixing_in_ptype_representation(self, solution: AbstractGASolutionRepresentation):
        slice_representation_solution: GASliceSolutionRepresentation = \
            GASliceSolutionRepresentation()
        slice_representation_solution = slice_representation_solution.from_common_representation(solution)

        slice_fixing = GaSliceRepresenationSolutionSimpleFillingFixing(self.res_configuration, self._application_graph)
        slice_representation_solution = slice_fixing.do_solution_fixing(slice_representation_solution)
        comm_solution = slice_representation_solution.to_common_representation()
        return self

        
    

        
    
    def __fixing_chip_core_in_ptype(self, ptype_solution):
        SLCIE_NEURON_FROM_INDEX = GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX
        SLCIE_NEURON_TO_INDEX = GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX
        CHIP_INDEX = GASliceSolutionRepresentation.CHIP_INDEX
        CORE_INDEX = GASliceSolutionRepresentation.CORE_INDEX

        slice_count = len(ptype_solution)
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

        # Built sdrams for all cores. Type: List[[chip_index: int, core_index: int, sdram: AbstractSDRAM, sdram_cost: int]]
        sdram_records = []
        chip_record_index = 0
        for chip_record in chip_core_records:
            chip_index = chip_record[0]
            if chip_index == -1:
                continue
            core_records = chip_record[1] # List[[core_id, slice_infos_data_frame]]
            for core_record in core_records:
                core_index = core_record[0]
                data_frames = core_record[1]
                slice_froms = list(data_frames[0])
                slice_tos = list(data_frames[1])
                # chip_core_location_identification = "%s#%s" % (chip_index, core_index)
                recorded_slice_count = len(slice_froms)
                if recorded_slice_count == 0:
                    continue                
                sdram = SolutionAdopter \
                    .calculate_sdram(self.get_application_vertex(slice_froms[0], slice_tos[0]), slice_froms[0], slice_tos[0])
                sdram_records.append([chip_index, core_index , sdram, sdram.get_total_sdram()])
                for i in range(1, recorded_slice_count):
                    sdram.merge(SolutionAdopter \
                        .calculate_sdram(None, slice_froms[i], slice_tos[i]))

        current_application_vertex_index = 0 
        application_vertices = self._application_graph.vertices
        application_vertex_neurons_index_presum = [0] * len(application_vertices)
        application_vertex_neurons_index_presum[0] = application_vertices[0].n_atoms()
        for i in range(1, len(application_vertices)):
            application_vertex_neurons_index_presum[i] = \
            application_vertex_neurons_index_presum[i - 1] + application_vertices[i].n_atoms()



        def set_core_chip(slice_index, allocated_chip_index, allocated_core_index):
            ptype_solution[slice_index][GASliceSolutionRepresentation.CHIP_INDEX] = allocated_chip_index

        # Create a map that map (chip_index, core_index) to (space usage)
        slice_index = 0
        while slice_index < slice_count:
            if ptype_solution[slice_index][GASliceSolutionRepresentation.CHIP_INDEX] != -1 and \
                ptype_solution[slice_index][GASliceSolutionRepresentation.CORE_INDEX] != -1:
                # Unnecessary to be processed.
                slice_index += 1
                continue
                
            slice_from = ptype_solution[slice_index][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX]
            slice_to = ptype_solution[slice_index][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX]
            slice_chip_index = ptype_solution[slice_index][GASliceSolutionRepresentation.CHIP_INDEX]
            slice_core_index = ptype_solution[slice_index][GASliceSolutionRepresentation.CORE_INDEX]
            
            # 1. Find the proper application vertex
            while slice_to >= application_vertex_neurons_index_presum[current_application_vertex_index]:
                current_application_vertex_index += 1

            application_vertex = application_vertices[current_application_vertex_index]
            sdram = None

            # split current slice to fix the constraint of max slice length when current slice's length exceed the maximun of slice length
            if slice_to - slice_from + 1 > self._max_slice_length[current_application_vertex_index]:
                slices_after_splitted = []
                while slice_from <= slice_to:
                    target_slice_to = min(slice_from + self._max_slice_length[current_application_vertex_index] - 1, slice_to)
                    slices_after_splitted.append[(slice_from, target_slice_to, slice_chip_index, slice_core_index)]
                del ptype_solution[slice_index]
                ptype_solution[slice_index:slice_index] = slices_after_splitted
                continue


            sdram = SolutionAdopter.calculate_sdram(application_vertex, slice_to - slice_from + 1)
            
            # 2. Find whether the same core of its left neighbor has enough space.
            if slice_index != 0:
                left_slice_from = ptype_solution[slice_index - 1][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX]
                left_slice_to = ptype_solution[slice_index - 1][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX]
                left_slice_chip_index = ptype_solution[slice_index - 1][GASliceSolutionRepresentation.CHIP_INDEX]
                left_slice_core_index = ptype_solution[slice_index - 1][GASliceSolutionRepresentation.CORE_INDEX]
                # find sdram
                ## linear search (TODO: binary search)
                success = False
                left_slice_location_in_sram_record = -1
                allocated_chip_index = -1
                allocated_core_index = -1
                # 1. find whether the core the left side slice of current slice prepared to be stored has enough space
                # to store current slice.
                for i in range(0, len(sdram_records)):
                    if(sdram_records[i][0] != left_slice_chip_index or sdram_records[i][1] != left_slice_core_index):
                        continue
                    left_slice_sdram = sdram_records[i][2]
                    left_slice_sdram_cost = sdram_records[i][3]
                    if left_slice_sdram_cost + sdram.get_total_sdram() > self.res_configuration.get_max_sdram():
                        break
                    left_slice_location_in_sram_record = i
                    left_slice_sdram.merge(sdram)
                    allocated_chip_index =  sdram_records[i][0]
                    allocated_core_index =  sdram_records[i][1]
                    success = True
                    break
                
                if success:
                    set_core_chip(slice_index, allocated_chip_index, allocated_core_index)
                    continue
                
                # 2. Find whether in the same chip the chip of the left slice
                # prepared to be stored there has a core that has enough space for storing 
                # the current slice, utilizing a greedy algorithm.
                pos = 0
                while pos < len(sdram_records):
                    if(sdram_records[pos][0] != left_slice_chip_index):
                        pos += 1
                        continue
                    j = pos + 1
                    while j < len(sdram_records) and sdram_records[j][0] == left_slice_chip_index:
                        j += 1
                    # sort sdram records of cores in the chip specified by 'left_slice_chip_index', according to 
                    # to recorded sdram cost (the 3rd element of a single record), ascending.
                    sdram_records[pos:j] = sorted(sdram_records[pos:j], key=lambda item:item[3], reverse=True)
                    break
                success = False
                while pos < len(sdram_records):
                    if(sdram_records[pos][0] != left_slice_chip_index):
                        break
                    sdram_in_record = sdram_records[pos][2]
                    sdram_cost_in_record = sdram_records[pos][3]
                    if sdram_cost_in_record + sdram_in_record.get_total_sdram() > self.res_configuration.get_max_sdram():
                        continue
                    sdram_in_record.merge(sdram)
                    allocated_chip_index = sdram_records[pos][0]
                    allocated_core_index = sdram_records[pos][1]
                    success = True

                if success:
                    set_core_chip(slice_index, allocated_chip_index, allocated_core_index)
                    continue

                # 3. Find whether there is a core that has enough space for storing current slice. Utilizes a greedy algorithm.
                sdram_records.sort(key=lambda item: item[3])
                success = False
                pos = 0
                while pos < len(sdram_records):
                    sdram_in_record = sdram_records[pos][2]
                    sdram_cost_in_record = sdram_records[pos][3]
                    if sdram_cost_in_record + sdram_in_record.get_total_sdram() > self.res_configuration.get_max_sdram():
                        pos += 1
                        continue
                    sdram_in_record.merge(sdram)
                    allocated_chip_index = sdram_records[pos][0]
                    allocated_core_index = sdram_records[pos][1]
                    success = True

                if success:
                    set_core_chip(slice_index, allocated_chip_index, allocated_core_index)
                    continue

                # 4. Try to find any chip that still can allocate a new core.
                last_pos = -1
                last_chip = -1
                success = False
                while pos < len(sdram_records):
                    chip = sdram_records[pos][0]
                    if last_pos == -1 or last_chip == -1:
                        last_pos = pos
                        pos += 1
                        continue
                    if chip == last_chip:
                        continue
                    else:
                        core_count = pos - last_pos
                        if core_count < self.res_configuration.get_max_cores_per_chip():
                            allocated_core_id = core_count
                            core_records.insert(pos, [slice_from, slice_to, chip, allocated_core_id])
                            success = True
                            allocated_chip_index = sdram_records[pos][0]
                            allocated_core_index = allocated_core_id
                            break

                if success:
                    set_core_chip(slice_index, allocated_chip_index, allocated_core_index)
                    break

                # 5. The worest situation. All chips are allocate all there cores.
                # And there is no exist a core that has enough space to store current slice.
                # In this situation, allocates a new chip.
                sdram_records.sort(key=lambda item:item[0])
                allocated_chip_index = sdram_records[-1][0] + 1 # New chip's index is set to the max index of current recorded chips' indexes + 1.
                allocated_core_index = 0
                if len(set([item[0] for item in chip_core_records])) > self.res_configuration.get_max_chips():
                    # We cannot find a legal configuration of this slice in the given resource constraints.
                    raise ValueError
                core_records.append(pos, [slice_from, slice_to, chip, allocated_core_id])
                set_core_chip(slice_index, allocated_chip_index, allocated_core_index)

    def __init__(self, resource_configuration: ResourceConfiguration, application_graph: ApplicationGraph) -> None:
        super().__init__()
        self.res_configuration = resource_configuration
        self._application_graph = application_graph
        # calculate max_slice_length
        self._max_slice_length = self._calculate_max_slice_lengths()

    def _calculate_max_slice_lengths(self) -> List[int]:
        def _calculate_max_slice_length(application_vertex) -> int:
            binary_search_left_pt = 0
            binary_search_right_pt = self.res_configuration.get_neruon_count() - 1
            while binary_search_left_pt <= binary_search_right_pt:
                m = (binary_search_right_pt - binary_search_left_pt) // 2 + binary_search_left_pt
                sdram = SolutionAdopter.calculate_sdram(application_vertex, m)
                if(sdram.get_total_sdram() == self.res_configuration.get_max_sdram()):
                    return m
                if(sdram.get_total_sdram() < self.res_configuration.get_max_sdram()):
                    binary_search_left_pt = m + 1
                    continue
                else:
                    binary_search_right_pt = m - 1
                    continue
            return binary_search_left_pt

        return [_calculate_max_slice_length(application_vertex) for application_vertex in self._application_graph.vertices]


    def _fixing_in_gtype_representation(self, solution: AbstractGASolutionRepresentation):
        raise NotImplementedError
    
    def __str__(self):
        return "slice_rep_fixing"