from .abst_ga_solution_representation import AbstractGASolutionRepresentation
from spinn_utilities.overrides import overrides
import numpy as np

class CommonGASolutionRepresentation(AbstractGASolutionRepresentation):
    def __init__(self, solution, max_cores_pre_chip, max_chips, use_ptype = False) -> None:
          super().__init__(solution, max_cores_pre_chip, max_chips, use_ptype)
          
    @overrides(AbstractGASolutionRepresentation.from_common_representation)
    def from_common_representation(self, solution: AbstractGASolutionRepresentation):
        self._solution = solution.get_solution()
        self._single_neuron_encoding_length = solution.get_single_neuron_encoding_length()
        self._max_chips = solution.get_max_chips()
        self._max_core_per_chip = solution.get_max_cores_per_chip()
        return self
    
    @overrides(AbstractGASolutionRepresentation.to_common_representation)
    def to_common_representation(self) -> AbstractGASolutionRepresentation:
        return CommonGASolutionRepresentation(self.get_solution(), self.get_max_cores_per_chip(),
            self.get_max_chips(), self.get_use_ptype())
    
    @overrides(AbstractGASolutionRepresentation._get_gtype_solution_representation)
    def _get_gtype_solution_representation(self):
        ptype_solution_rep = self.get_solution()
        single_neuron_encoding_lentgh = self.get_single_neuron_encoding_length()
        solution = bytearray(len(ptype_solution_rep) * single_neuron_encoding_lentgh)
        neuron_count = len(ptype_solution_rep)
        for neuron_index in range(0, neuron_count):
            neuron_encoding_offset_from = neuron_index * single_neuron_encoding_lentgh
            neuron_encoding_offset_to = (neuron_index + 1) * single_neuron_encoding_lentgh
            neuron_encoding_binary_str = ('{0:' + str(single_neuron_encoding_lentgh) + 'b}').format(ptype_solution_rep[neuron_index])
            solution[neuron_encoding_offset_from:neuron_encoding_offset_to] = neuron_encoding_binary_str

    @overrides(AbstractGASolutionRepresentation._get_ptype_solution_representation)
    def _get_ptype_solution_representation(self):
        solution = []
        gtype_solution_rep = self.get_solution()
        single_neuron_encoding_lentgh = self.get_single_neuron_encoding_length()
        neuron_count = len(gtype_solution_rep) / single_neuron_encoding_lentgh
        
        for neuron_index in range(0, neuron_count):
            neuron_encoding_offset_from = neuron_index * single_neuron_encoding_lentgh
            neuron_encoding_offset_to = (neuron_index + 1) * single_neuron_encoding_lentgh
            neuron_encoding_binary_str = self._solution[neuron_encoding_offset_from:neuron_encoding_offset_to]
            solution.append(int(neuron_encoding_binary_str, 2))
        return solution
    
    @overrides(AbstractGASolutionRepresentation._set_new_solution_data_in_ptype)
    def _set_new_solution_data_in_ptype(self, solution_data):
        if not isinstance(solution_data, list):
            raise TypeError
        self._solution.clear()
        self._solution.append(solution_data)

    @overrides(AbstractGASolutionRepresentation._set_new_solution_data_in_gtype)
    def _set_new_solution_data_in_gtype(self, solution_data):
        if not isinstance(solution_data, bytearray):
            raise TypeError
        self._solution.clear()
        self._solution.append(solution_data)
    
    @classmethod
    def class_str(self):
        return "comm_rep"
    
    def __str__(self):
        return CommonGASolutionRepresentation.class_str(self)
    
    @overrides(AbstractGASolutionRepresentation.get_serialized_data)
    def get_serialized_data(self):
            return [CommonGASolutionRepresentation.class_str(), self._use_ptype, self._max_chips, self._max_cores_per_chip, self.get_solution()]
