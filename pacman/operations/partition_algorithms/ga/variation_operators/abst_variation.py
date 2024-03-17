from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
class AbstractGaVariation(object):
    def do_variation(self, individual: AbstractGASolutionRepresentation) -> AbstractGASolutionRepresentation:
        return self._do_variation(individual)
    
    def _do_variation(self, individual: AbstractGASolutionRepresentation) -> AbstractGASolutionRepresentation:
        raise NotImplementedError


    def __str__(self):
        return "abst_variation"