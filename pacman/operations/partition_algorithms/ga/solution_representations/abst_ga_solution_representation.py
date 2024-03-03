from .common_ga_solution_representation import CommonGASolutionRepresentation
class AbstractGASolutionRepresentation:
    def __init__(self, solution, max_cores_pre_chip, max_chips, use_ptype = True) -> None:
        self._use_ptype = use_ptype
        self._solution = solution
        self._max_cores_per_chip = max_cores_pre_chip
        self._max_chips = max_chips

    def get_ptype_solution(self):
        if self._use_ptype:
            self._solution
        return self._get_ptyte_solution()

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
   
    def _get_ptyte_solution(self):
        raise NotImplementedError
    
    def _get_gtyte_solution(self):
        raise NotImplementedError
    
    def __str__(self):
        return "abst_rep"