from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
class AbstractGaVariation(object):
    def do_variation(self, solution: AbstractGASolutionRepresentation) -> AbstractGASolutionRepresentation:
        raise NotImplementedError
    
    def __str__(self):
        return "abst_variation"