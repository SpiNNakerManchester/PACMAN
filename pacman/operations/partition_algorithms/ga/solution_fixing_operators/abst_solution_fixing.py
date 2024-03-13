from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
class AbstractGaSolutionFixing(object):
    def do_solution_fixing(self, solution: AbstractGASolutionRepresentation) -> AbstractGASolutionRepresentation:
        return self._do_solution_fixing(solution)
            
    def _do_solution_fixing(self, solution: AbstractGASolutionRepresentation) -> AbstractGASolutionRepresentation:
        raise NotImplementedError
    
    def __str__(self):
        return "abst_solution_fix"
    

        