from pacman.operations.placer_algorithms.abstract_placer_algorithm import\
    AbstractPlacerAlgorithm


class RadialPlacer(AbstractPlacerAlgorithm):
    """ An radial algorithm that can place a subgraph onto a machine based off a
    circle out behaviour from a ethernet at 0 0
    """

    def __init__(self):
        """constructor to build a
        pacman.operations.placer_algorithms.RadialPlacer.RadialPlacer
        <params to be filled in when implimented>
        """
        pass

    def place(self, subgraph, machine):
        """ Place a subgraph so that each subvertex is placed on a core

        :param subgraph: The subgraph to place
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :param machine: The machine on which to place the graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :return: A set of placements
        :rtype: :py:class:`pacman.model.placements.placements.Placements`
        :raise pacman.exceptions.PacmanPlaceException: If something\
                   goes wrong with the placement
        """
        pass