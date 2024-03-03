from .common_ga_solution_representation import CommonGASolutionRepresentation
import numpy as np
class AbstractGASolutionRepresentation:
    def __init__(self, solution, max_cores_pre_chip, max_chips, use_ptype = True) -> None:
        self._use_ptype = use_ptype
        self._solution = solution
        self._max_cores_per_chip = max_cores_pre_chip
        self._max_chips = max_chips
        self._single_neuron_encoding_length = \
            (int)(np.ceil(np.log2(self.get_max_chips() * self.get_max_core_per_chip)))
   
    def get_ptype_solution(self) -> bytearray:
        if self._use_ptype:
            self._solution
        return self._get_ptype_solution()


    def get_single_neuron_encoding_length(self):
        return self._single_neuron_encoding_length

    def get_gtype_solution(self):
        if self._use_ptype:
            return self._get_gtyte_solution()
        return self._solution
    
    def get_solution(self):
        return self._solution
    
    def get_max_chips(self):
        return self._max_chips
    
    def get_max_cores_per_chip(self):
        return self._max_cores_per_chip
    
    def get_use_ptype(self):
        return self._use_ptype

    def get_solution(self):
        return self._solution
    
    
    def from_common_representation(self, solution: CommonGASolutionRepresentation):
        raise NotImplementedError
    
    def to_common_representation(self) -> CommonGASolutionRepresentation:
        raise NotImplementedError
   
    def _get_ptype_solution(self):
        raise NotImplementedError
    
    def _get_gtyte_solution(self):
        raise NotImplementedError
    
    def __str__(self):
        return "abst_rep"