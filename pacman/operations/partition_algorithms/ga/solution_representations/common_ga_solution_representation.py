from .abst_ga_solution_representation import AbstractGASolutionRepresentation
from spinn_utilities.overrides import overrides
class CommonGASolutionRepresentation(AbstractGASolutionRepresentation):
    def __init__(self, byte_array_solution: bytearray, single_neuron_encoding_length, max_cores_pre_chip, max_chips) -> None:
          super().__init__()
          self._solution = byte_array_solution
          self._single_neuron_encoding_length = single_neuron_encoding_length
          self._max_chip = max_chips
          self._max_core_per_chip = max_cores_pre_chip

    def get_max_chip(self):
        return self._max_chip
    
    def get_max_core_per_chip(self):
        return self._max_core_per_chip
    
    def get_single_neuron_encoding_length(self):
        return self._single_neuron_encoding_length

    def get_solution(self):
        return self._solution

    @overrides(AbstractGASolutionRepresentation.get_npy_data)
    def get_npy_data(self):
        raise NotImplementedError

    @overrides(AbstractGASolutionRepresentation.convert_from_common_representation)
    def convert_from_common_representation(self, solution):
        raise NotImplementedError    

    def __str__(self):
            return "comm_rep"