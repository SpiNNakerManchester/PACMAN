from .abst_ga_solution_representation import AbstractGASolutionRepresentation
from .common_ga_solution_representation import CommonGASolutionRepresentation
from spinn_utilities.overrides import overrides
class GASliceSolutionRepresentation(AbstractGASolutionRepresentation):
    def __init__(self) -> None:
          super().__init__()
          self._solution = [] # List[List[(slice_neuron_from, slice_neuron_to, chip_index, core_index)]]
          self._max_cores_per_chip = -1
          self._max_chips = -1
          self._single_neuron_encoding_length = -1

    def __init__(self, slices_end_points, slices_chip_indexes, slices_core_indexes, max_cores_per_chip, max_chips, single_neuron_encoding_length) -> None:
          super().__init__()
          self._solution = []
          self._max_cores_per_chip = max_cores_per_chip
          self._max_chips = max_chips
          self._single_neuron_encoding_length = single_neuron_encoding_length
          previous_pos = 0
          slice_index = 0
          for endpoint in slices_end_points:
               slice_neuron_from = previous_pos
               slice_neuron_to = endpoint
               chip_index = slices_chip_indexes[slice_index]
               core_index = slices_core_indexes[slice_index]
               slice_index += 1
               self._solution.append((slice_neuron_from, slice_neuron_to, chip_index, core_index))


    @overrides(AbstractGASolutionRepresentation.get_npy_data)
    def get_npy_data(self):
        raise NotImplementedError

    @overrides(AbstractGASolutionRepresentation.get_solution)
    def get_solution(self):
        return self._solution

    @overrides(AbstractGASolutionRepresentation.convert_to_gtype_representation)
    def convert_to_gtype_representation(self) -> bytearray:
        solution = self._solution
        gtype_length = len(solution) * 32 * 4
        gtype_represent = bytearray(gtype_length)
        for i in range(0, len(solution)):
            binary_string_len32 = ('{0:32b}').format(solution[i / 4][i % 4])
            gtype_represent[i * 32: (i + 1) * 32] = binary_string_len32
        return gtype_represent
    
    @overrides(AbstractGASolutionRepresentation.convert_to_ptype_from_gtype_representation)
    def convert_to_ptype_from_gtype_representation(self, gtype_solution_representation) -> bytearray:
        gtype_length = len(gtype_solution_representation)
        solution = []
        slice_info = []
        for int32_index in range(0, gtype_length / 32):
            slice_info.append(int(gtype_solution_representation[int32_index * 32, (int32_index + 1) * 32], 2))
            if(len(slice_info) == 4):
                 solution.append(slice_info)
                 slice_info = []
        return solution

    @overrides(AbstractGASolutionRepresentation.convert_to_common_representation)
    def convert_to_common_representation(self):
        solution = self.get_solution()
        single_neuron_encoding_length = self._single_neuron_encoding_length
        comm_solution = bytearray(single_neuron_encoding_length)
        neuron_index = 0
        for i in range(0, len(solution)):
            slice_info = solution[i]
            slice_neuron_from = slice_info[0]
            slice_neuron_to = slice_info[1]
            chip_index = slice_info[2]
            core_index = slice_info[3]
            write_common_solution_from = slice_neuron_from * single_neuron_encoding_length
            write_common_solution_to = (slice_neuron_to + 1) * single_neuron_encoding_length
            chip_core_represent = chip_index * self._max_cores_per_chip + core_index
            slice_length = slice_neuron_to - slice_neuron_from + 1
            binary_string = ('{0:' + str(single_neuron_encoding_length) + 'b}').format(chip_core_represent) * slice_length

            comm_solution[write_common_solution_from:write_common_solution_to] = binary_string
        return CommonGASolutionRepresentation(comm_solution, single_neuron_encoding_length, self._max_cores_per_chip, self._max_chips)


    
    @overrides(AbstractGASolutionRepresentation.convert_from_common_representation)
    def convert_from_common_representation(self, solution: CommonGASolutionRepresentation):
        self._solution = []
        solution_in_bytes_representation = solution.get_solution()
        single_neuron_encoding_length = solution.get_single_neuron_encoding_length()
        bytearray_length = len(solution_in_bytes_representation)
        neuron_count = bytearray_length / single_neuron_encoding_length
        pos = 0
        max_chips = solution.get_max_chip()
        max_cores_per_chip = solution.get_max_core_per_chip()
        last_chip_index = -1
        last_core_index = -1
        last_neuron_index = -1
        self._max_chips = max_chips
        self._max_cores_per_chip = max_cores_per_chip
        self._single_neuron_encoding_length = solution.get_single_neuron_encoding_length()

        solution_in_bytes_representation.extend('1' * single_neuron_encoding_length)
        
        for neuron_index in range(0, neuron_count + 1):
            nueron_loc_encoding_from = neuron_index * single_neuron_encoding_length
            neuron_loc_encoding_to = (neuron_index + 1) * single_neuron_encoding_length
            neuron_loc_binary_string_rep = solution_in_bytes_representation[nueron_loc_encoding_from: neuron_loc_encoding_to].decode()
            neuron_loc_int_rep = int(neuron_loc_binary_string_rep, 2)
            chip_index = neuron_loc_int_rep / max_cores_per_chip
            core_index = neuron_loc_int_rep % max_cores_per_chip
            if last_chip_index == -1 or last_core_index == -1 or last_neuron_index == -1:
                last_chip_index = chip_index
                last_core_index = core_index
                last_neuron_index = neuron_index
                continue

            if chip_index == last_chip_index and core_index == last_core_index:
                continue
            
            self._solution.append([last_neuron_index, neuron_index - 1, last_chip_index, last_core_index])

            last_neuron_index = neuron_index
            last_chip_index = chip_index
            last_core_index = core_index

        del solution_in_bytes_representation[-single_neuron_encoding_length:]
        
        return self

            
            
                 

    def __str__(self):
            return "comm_rep"