from .abst_ga_solution_representation import AbstractGASolutionRepresentation
from .common_ga_solution_representation import CommonGASolutionRepresentation
from spinn_utilities.overrides import overrides
import numpy as np

# PTYPE := List[(slice_neuron_from: int, slice_neuron_to: int, chip_index: int, core_index: int)]
class GASliceSolutionRepresentation(AbstractGASolutionRepresentation):
    SLICE_NEURON_FROM_INDEX = 0
    SLICE_NEURON_TO_INDEX = 1
    CHIP_INDEX = 2
    CORE_INDEX = 3

    def __init__(self, data_for_build_solution, slices_chip_indexes, slices_core_indexes, max_cores_per_chip, max_chips, use_ptype=True) -> None:
          super().__init__([], max_cores_per_chip, max_chips, use_ptype)
          # When it not use a ptype representation of solution data, 
          #     the data_for_build_solution should be a bytearray that each slice's neuron_id_from, neuron_id_to, chip_id and core_id are encoded.
          # Specifically, it would be a bytearray with length of (4 * 32 * slice_count).
          # Each of neuron_id_from, neuron_id_to, chip_id and core_id are encoded to a string with length of 32, representing the 32-bit binary representation of that slice 
          #     information element.
          # 128 bytes from (4 * 32 * i) to (4 * 32 * (i + 1)) encodes the i-th slice's neuron_id_from, neuron_id_to, chip_id and core_id. 

          if not use_ptype:
              self._solution = data_for_build_solution
              return
          previous_pos = 0
          slice_index = 0
          
          for endpoint in data_for_build_solution:
               slice_neuron_from = previous_pos
               slice_neuron_to = endpoint
               chip_index = slices_chip_indexes[slice_index]
               core_index = slices_core_indexes[slice_index]
               slice_index += 1
               previous_pos = slice_neuron_to + 1 
               self._solution.append([slice_neuron_from, slice_neuron_to, chip_index, core_index])

    def get_slice_neuron_from_in_slice_info(self, slice_info_index):
        if self._use_ptype:
           return self._solution[slice_info_index][self.SLICE_NEURON_FROM_INDEX]
        raise NotImplementedError
    
    def get_slice_neuron_to_index_in_slice_info(self, slice_info_index):
        if self._use_ptype:
           return self._solution[slice_info_index][self.SLICE_NEURON_TO_INDEX]
        raise NotImplementedError

    def get_chip_index_in_slice_info(self, slice_info_index):
        if self._use_ptype:
           return self._solution[slice_info_index][self.CHIP_INDEX]
        raise NotImplementedError

    def get_core_index_in_slice_info(self, slice_info_index):
         if self._use_ptype:
            return self._solution[slice_info_index][self.CORE_INDEX]
         raise NotImplementedError

    def set_slice_neuron_from_in_slice_info(self, slice_info_index, value):
         if self._use_ptype:
            self._solution[slice_info_index][self.SLICE_NEURON_FROM_INDEX] = value
         raise NotImplementedError

    def set_slice_neuron_to_in_slice_info(self, slice_info_index, value):
         if self._use_ptype:
            self._solution[slice_info_index][self.SLICE_NEURON_TO_INDEX] = value
         raise NotImplementedError

    def set_chip_index_in_slice_info(self, slice_info_index, value):
         if self._use_ptype:
            self._solution[slice_info_index][self.CHIP_INDEX] = value
         raise NotImplementedError

    def set_core_index_in_slice_info(self, slice_info_index, value):
         if self._use_ptype:
            self._solution[slice_info_index][self.CORE_INDEX] = value
         raise NotImplementedError

    @overrides(AbstractGASolutionRepresentation._get_gtype_solution_representation)
    def _get_gtype_solution_representation(self) -> bytearray:
        solution = self._solution
        gtype_length = len(solution) * 32 * 4
        gtype_represent = bytearray(gtype_length)
        for i in range(0, len(solution)):
            for j in range(0, 4):
                binary_string_len32 = ('{0:32b}').format(solution[i][j])
                gtype_represent[(i * 4 + j) * 32: (i * 4 + j + 1) * 32] = bytearray(binary_string_len32.encode('ascii'))
        return gtype_represent
    
    @overrides(AbstractGASolutionRepresentation._get_ptype_solution_representation)
    def _get_ptype_solution_representation(self):
        gtype_solution_representation = self.get_solution()
        gtype_length = len(gtype_solution_representation)
        solution = []
        slice_info = []
        for neuron_index in range(0, gtype_length / 32):
            slice_info.append(int(gtype_solution_representation[neuron_index * 32, (neuron_index + 1) * 32], 2))
            if(len(slice_info) == 4):
                 solution.append((*slice_info, ))
                 slice_info = []
        return solution

    @overrides(AbstractGASolutionRepresentation.to_common_representation)
    def to_common_representation(self):
        solution = self.get_solution()
        if not self._use_ptype:
            raise NotImplemented
        common_solution = []
        for i in range(0, len(solution)):
            slice_info = solution[i]
            slice_neuron_from = slice_info[GASliceSolutionRepresentation.SLICE_NEURON_FROM_INDEX]
            slice_neuron_to = slice_info[GASliceSolutionRepresentation.SLICE_NEURON_TO_INDEX]
            chip_index = slice_info[GASliceSolutionRepresentation.CHIP_INDEX]
            core_index = slice_info[GASliceSolutionRepresentation.CORE_INDEX]
            write_common_solution_from = slice_neuron_from
            write_common_solution_to = (slice_neuron_to + 1)
            chip_core_represent = chip_index * self._max_cores_per_chip + core_index
            slice_length = slice_neuron_to - slice_neuron_from + 1
            
            common_solution[write_common_solution_from:write_common_solution_to] = chip_core_represent
        return CommonGASolutionRepresentation(common_solution, 1, self._max_cores_per_chip, self._max_chips, True)

    @overrides(AbstractGASolutionRepresentation.from_common_representation)
    def from_common_representation(self, solution: CommonGASolutionRepresentation):
        self._solution = []
        solution_in_bytes_representation = solution.get_ptype_solution_representation()
        single_neuron_encoding_length = solution.get_single_neuron_encoding_length()
        bytearray_length = len(solution_in_bytes_representation)
        neuron_count = bytearray_length / single_neuron_encoding_length
        max_chips = solution.get_max_chips()
        max_cores_per_chip = solution.get_max_cores_per_chip()
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
    
    @overrides(AbstractGASolutionRepresentation._set_new_solution_data_in_ptype)
    def _set_new_solution_data_in_ptype(self, solution_data):
        if not isinstance(solution_data, list):
            raise TypeError
        self._solution.clear()
        self._solution += solution_data

    @overrides(AbstractGASolutionRepresentation._set_new_solution_data_in_gtype)
    def _set_new_solution_data_in_gtype(self, solution_data):
        if not isinstance(solution_data, bytearray):
            raise TypeError
        self._solution.clear()
        self._solution.append(solution_data)

    @overrides(AbstractGASolutionRepresentation.get_serialized_data)
    def get_serialized_data(self):
        if self._use_ptype:
            solution_data = self.get_solution()
            return [GASliceSolutionRepresentation.class_str(), self._use_ptype, self._max_chips, self._max_cores_per_chip, \
                    [slice_info[self.SLICE_NEURON_TO_INDEX] for slice_info in solution_data],\
                    [slice_info[self.CHIP_INDEX] for slice_info in solution_data], \
                    [slice_info[self.CORE_INDEX] for slice_info in solution_data]]
        else:
            return [GASliceSolutionRepresentation.class_str(), self._use_ptype, self._max_chips, self._max_cores_per_chip, self.get_solution()]
    
    @classmethod
    def class_str(self):
        return "slice_rep"
    
    def __str__(self):
        return GASliceSolutionRepresentation.class_str()
    

    