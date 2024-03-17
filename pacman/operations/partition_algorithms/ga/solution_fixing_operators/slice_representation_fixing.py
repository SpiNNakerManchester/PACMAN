from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_fixing_operators.abst_solution_fixing import AbstractGaSolutionFixing
from pacman.operations.partition_algorithms.ga.solution_representations.slice_representation import GASliceSolutionRepresentation
from typing import Tuple, List
from spinn_utilities.overrides import overrides
from pacman.operations.partition_algorithms.ga.entities.resource_configuration import ResourceConfiguration
import pandas as pd
from pacman.operations.partition_algorithms.solution_adopter import SolutionAdopter
from pacman.model.graphs.application import ApplicationGraph
from pacman.data import PacmanDataView

class GaSliceRepresenationSolutionSimpleFillingFixing(AbstractGaSolutionFixing):
    @overrides(AbstractGaSolutionFixing._do_solution_fixing)
    def _do_solution_fixing(self, solution: AbstractGASolutionRepresentation) -> AbstractGASolutionRepresentation:
        if not isinstance(solution, GASliceSolutionRepresentation):
            raise TypeError
        if solution._use_ptype:
            return self._fixing_in_ptype_representation(solution)
        else:
            return self._fixing_in_gtype_representation(solution)


    def _fixing_in_ptype_representation(self, solution: AbstractGASolutionRepresentation):
        global application_vertexes_index
        global new_ptype_representation
        ptype_representation: List[Tuple] = solution.get_ptype_solution_representation() 

        # 1. Ensure slice's ending >= slice's beginning
        for i in range(0, len(ptype_representation)):
            if ptype_representation[i][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX] < ptype_representation[i][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX]:
                t = ptype_representation[i][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX]
                ptype_representation[i][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX] = ptype_representation[i][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX]
                ptype_representation[i][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX] = t

        # 2. Sort by each slice's beginning
        ptype_representation.sort(key = lambda slice_info: slice_info[GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX])
        ptype_representation_length = len(ptype_representation)
        new_ptype_representation = []
        pt = 1
        last_slice_neuron_index_from = ptype_representation[0][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX]
        last_slice_neuron_index_to = ptype_representation[0][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX]
        new_ptype_representation.append(ptype_representation[0])
        application_vertexes = list(self._application_graph.vertices)
        application_vertexes_prefix_sum = [0] * len(application_vertexes)
        application_vertexes_prefix_sum[0] = application_vertexes[0].n_atoms
        for i in range(1, len(application_vertexes)):
            application_vertexes_prefix_sum[i] = application_vertexes_prefix_sum[i - 1] + application_vertexes[i].n_atoms
        
        application_vertexes_index = 0

        def append_slice_with_considering_application_vertexes_ending(slice_neuron_index_from, slice_neuron_index_to, chip_index, core_index, index = -1):
            global application_vertexes_index
            global new_ptype_representation
            current_application_vertex_max_neuron_index = application_vertexes_prefix_sum[application_vertexes_index] - 1
            neuron_index_from = slice_neuron_index_from
            neuron_index_to = slice_neuron_index_to
            inserted = 0
            while neuron_index_to > current_application_vertex_max_neuron_index:
                new_ptype_representation.append([\
                                    slice_neuron_index_from,\
                                    current_application_vertex_max_neuron_index,\
                                    ptype_representation[pt][GASliceSolutionRepresentation.CHIP_INDEX],\
                                    ptype_representation[pt][GASliceSolutionRepresentation.CORE_INDEX]])
                slice_neuron_index_from = application_vertexes_prefix_sum[application_vertexes_index]
                application_vertexes_index += 1
                current_application_vertex_max_neuron_index = application_vertexes_prefix_sum[application_vertexes_index]
                inserted += 1

            # it necessary has condition slice_neuron_index_from <= slice_neuron_index_to.
            new_ptype_representation.append([\
                                    slice_neuron_index_from,\
                                    slice_neuron_index_to,\
                                    chip_index,\
                                    core_index])
            inserted += 1
            if index != -1:
                appended = new_ptype_representation[-inserted:]
                new_ptype_representation = new_ptype_representation[:len(new_ptype_representation) - inserted]
                new_ptype_representation[index:index] = appended

        while pt < ptype_representation_length:
            slice_neuron_index_from = ptype_representation[pt][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX]
            slice_neuron_index_to = ptype_representation[pt][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX]
            if slice_neuron_index_from < 0:
                continue
            if slice_neuron_index_from >= self._resourcr_constraint_configuration.get_neruon_count() or slice_neuron_index_to >= \
                                                                        self._resourcr_constraint_configuration.get_neruon_count():
                break
            
            if slice_neuron_index_from == last_slice_neuron_index_to + 1:
                # No need any processing.
                append_slice_with_considering_application_vertexes_ending(slice_neuron_index_from,\
                                                                          slice_neuron_index_to,\
                                                                          ptype_representation[pt][GASliceSolutionRepresentation.CHIP_INDEX],\
                                                                          ptype_representation[pt][GASliceSolutionRepresentation.CORE_INDEX])
                last_slice_neuron_index_from = ptype_representation[pt][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX]
                last_slice_neuron_index_to = ptype_representation[pt][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX]

                pt += 1
                continue

            if slice_neuron_index_from > last_slice_neuron_index_to + 1:
                # Fill vacancy. (Chip index and core index's decision are pending.)
                append_slice_with_considering_application_vertexes_ending(last_slice_neuron_index_to + 1, slice_neuron_index_from - 1, -1, -1)
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
                append_slice_with_considering_application_vertexes_ending(new_current_slice_from + 1, slice_neuron_index_to, -1, -1)
                last_slice_neuron_index_from = new_current_slice_from
                last_slice_neuron_index_to = slice_neuron_index_to
                
                pt += 1
                continue
        
        # Fill Vacancy of the beginning part and the ending part
        if new_ptype_representation[0][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX] > 0:
            append_slice_with_considering_application_vertexes_ending(0, (0, new_ptype_representation[0][GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX - 1], -1, -1, 0))
        if new_ptype_representation[-1][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX] < self._resourcr_constraint_configuration.get_neruon_count() - 1:
            append_slice_with_considering_application_vertexes_ending(new_ptype_representation[-1][GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX] + 1, self._resourcr_constraint_configuration.get_neruon_count() - 1, -1, -1)        
        self.__fixing_chip_core_in_ptype(new_ptype_representation)

        chip_index_remapping_lookup_table = dict({})

        # Remapping chip_index, make chip index in used are contiguous.
        keys = list(set([item[GASliceSolutionRepresentation.CHIP_INDEX] for item in new_ptype_representation]))
        for i in range(0, len(keys)):
            chip_index_remapping_lookup_table[keys[i]] = i
        for i in range(0, len(new_ptype_representation)):
            new_ptype_representation[i][GASliceSolutionRepresentation.CHIP_INDEX] = \
                chip_index_remapping_lookup_table[new_ptype_representation[i][GASliceSolutionRepresentation.CHIP_INDEX]]
            
        # Update the solution
        # TODO: pull the `set_new_ptype_representation_solution` to abstract class
        solution.set_new_representation_solution(new_ptype_representation)
        return solution
        
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
        slices_data_frame[slices_data_frame["core_id"] > self._resourcr_constraint_configuration.get_max_cores_per_chip()] = -1
        slices_data_frame[slices_data_frame["chip_id"] < 0] = -1
        slices_data_frame[slices_data_frame["chip_id"] > self._resourcr_constraint_configuration.get_max_chips()] = -1


        # 2. Make all slice's size can be fitted in a core.


        # 3. Make lookup table for searching slices by using (core_index, chip_index) pair.
            # Slices are represented by DataFrame.
            # DataFrames are sort by chip_index and core_index.

            # grouped_result: List[List[chip_core_identification: int, List[core_index, slice_infos: DataFrame]]]
        
        chip_core_records = \
            sorted([
                        [chip_index,
                            sorted([
                                [core_index, chip_core_df] \
                                for core_index, chip_core_df \
                                in chip_df.groupby('core_id')
                            ], key=lambda x: x[0]) # sort each chip's records by core_index
                        ]
                    for chip_index, chip_df
                    in slices_data_frame.groupby('chip_id')
            ], key=lambda x: x[0])

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
                sdram_records.append([chip_index, core_index , sdram, sdram.get_total_sdram(PacmanDataView.get_plan_n_timestep())])
                for i in range(1, recorded_slice_count):
                    sdram.merge(SolutionAdopter \
                        .calculate_sdram(None, slice_froms[i], slice_tos[i]))

        current_application_vertex_index = 0 
        application_vertices = list(self._application_graph.vertices)
        application_vertex_neurons_index_presum = [0] * len(application_vertices)
        application_vertex_neurons_index_presum[0] = application_vertices[0].n_atoms
        
        for i in range(1, len(application_vertices)):
            application_vertex_neurons_index_presum[i] = \
            application_vertex_neurons_index_presum[i - 1] + application_vertices[i].n_atoms

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
                    # TODO: ensure there exist enough space for a SDRAM ro store the slice prepared to be inserted.
                    slices_after_splitted.append([slice_from, target_slice_to, slice_chip_index, slice_core_index])
                del ptype_solution[slice_index]
                ptype_solution[slice_index:slice_index] = slices_after_splitted
                slice_index += 1
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
                    if left_slice_sdram_cost + sdram.get_total_sdram(PacmanDataView.get_plan_n_timestep()) > self._resourcr_constraint_configuration.get_max_sdram():
                        break
                    left_slice_location_in_sram_record = i
                    left_slice_sdram.merge(sdram)
                    allocated_chip_index =  sdram_records[i][0]
                    allocated_core_index =  sdram_records[i][1]
                    success = True
                    break
                
                if success:
                    set_core_chip(slice_index, allocated_chip_index, allocated_core_index)
                    slice_index += 1
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
                    if sdram_cost_in_record + sdram_in_record.get_total_sdram(PacmanDataView.get_plan_n_timestep()) > self._resourcr_constraint_configuration.get_max_sdram():
                        continue
                    sdram_in_record.merge(sdram)
                    allocated_chip_index = sdram_records[pos][0]
                    allocated_core_index = sdram_records[pos][1]
                    success = True

                if success:
                    set_core_chip(slice_index, allocated_chip_index, allocated_core_index)
                    slice_index += 1
                    continue

                # 3. Find whether there is a core that has enough space for storing current slice. Utilizes a greedy algorithm.
                sdram_records.sort(key=lambda item: item[3])
                success = False
                pos = 0
                while pos < len(sdram_records):
                    sdram_in_record = sdram_records[pos][2]
                    sdram_cost_in_record = sdram_records[pos][3]
                    if sdram_cost_in_record + sdram_in_record.get_total_sdram(PacmanDataView.get_plan_n_timestep()) > self._resourcr_constraint_configuration.get_max_sdram():
                        pos += 1
                        continue
                    sdram_in_record.merge(sdram)
                    allocated_chip_index = sdram_records[pos][0]
                    allocated_core_index = sdram_records[pos][1]
                    success = True

                if success:
                    set_core_chip(slice_index, allocated_chip_index, allocated_core_index)
                    slice_index += 1
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
                        if core_count < self._resourcr_constraint_configuration.get_max_cores_per_chip():
                            allocated_core_id = core_count
                            core_records.insert(pos, [slice_from, slice_to, chip, allocated_core_id])
                            success = True
                            allocated_chip_index = sdram_records[pos][0]
                            allocated_core_index = allocated_core_id
                            break

                if success:
                    set_core_chip(slice_index, allocated_chip_index, allocated_core_index)
                    slice_index += 1
                    break

                # 5. The worest situation. All chips are allocate all there cores.
                # And there is no exist a core that has enough space to store current slice.
                # In this situation, allocates a new chip.
                sdram_records.sort(key=lambda item:item[0])
                allocated_chip_index = sdram_records[-1][0] + 1 # New chip's index is set to the max index of current recorded chips' indexes + 1.
                allocated_core_index = 0
                if len(set([item[0] for item in chip_core_records])) > self._resourcr_constraint_configuration.get_max_chips():
                    # We cannot find a legal configuration of this slice in the given resource constraints.
                    raise ValueError
                core_records.append(pos, [slice_from, slice_to, chip, allocated_core_id])
                set_core_chip(slice_index, allocated_chip_index, allocated_core_index)
                slice_index += 1
                

    def __init__(self, resource_constraint_configuration: ResourceConfiguration, application_graph: ApplicationGraph) -> None:
        super().__init__()
        self._resourcr_constraint_configuration = resource_constraint_configuration
        self._application_graph = application_graph
        # calculate max_slice_length
        self._max_slice_length = self._calculate_max_slice_lengths()

    def _calculate_max_slice_lengths(self) -> List[int]:
        
        def _calculate_max_slice_length(application_vertex) -> int:
            binary_search_left_pt = 0
            binary_search_right_pt = self._resourcr_constraint_configuration.get_neruon_count() - 1
            while binary_search_left_pt <= binary_search_right_pt:
                m = (binary_search_right_pt - binary_search_left_pt) // 2 + binary_search_left_pt
                sdram = SolutionAdopter.calculate_sdram(application_vertex, m)
                if(sdram.get_total_sdram(PacmanDataView.get_plan_n_timestep()) == self._resourcr_constraint_configuration.get_max_sdram()):
                    return m
                if(sdram.get_total_sdram(PacmanDataView.get_plan_n_timestep()) < self._resourcr_constraint_configuration.get_max_sdram()):
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