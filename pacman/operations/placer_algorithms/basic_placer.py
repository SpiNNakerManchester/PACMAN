from pacman.operations.placer_algorithms.abstract_placer_algorithm import\
    AbstractPlacerAlgorithm
from pacman.model.constraints.placer_chip_and_core_constraint \
    import PlacerChipAndCoreConstraint
from pacman.model.constraints.placer_subvertex_same_chip_constraint \
    import PlacerSubvertexSameChipConstraint
from pacman.model.placements.placements import Placements
from pacman import exceptions

import logging

logger = logging.getLogger(__name__)


class BasicPlacer(AbstractPlacerAlgorithm):
    """ An basic algorithm that can place a subgraph onto a machine based off a
    raster behaviour
    """

    def __init__(self, machine, graph):
        """constructor to build a \
        pacman.operations.placer_algorithms.BasicPlacer.BasicPlacer
        :param machine: The machine on which to place the graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        """
        AbstractPlacerAlgorithm.__init__(self, machine, graph)
        self._supported_constrants.append(PlacerChipAndCoreConstraint)
        self._supported_constrants.append(PlacerSubvertexSameChipConstraint)

    def place(self, subgraph, graph_to_subgraph_mapper):
        """ Place a subgraph so that each subvertex is placed on a core

        :param subgraph: The subgraph to place
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :param graph_to_subgraph_mapper: the mappings between graph and subgraph
        :type graph_to_subgraph_mapper:
        pacman.model.graph_subgraph_mapper.graph_subgraph_mapper.GraphSubgraphMapper
        :return: A set of placements
        :rtype: :py:class:`pacman.model.placements.placements.Placements`
        :raise pacman.exceptions.PacmanPlaceException: If something\
                   goes wrong with the placement
        """
        #check that the algorithum can handle the constraints
        self._check_can_support_constraints(subgraph)

        placements = Placements()
        ordered_subverts = \
            self.sort_subverts_by_constraint_authority(subgraph.subvertices)

        # Iterate over subvertices and generate placements
        for subvertex in ordered_subverts:

            # Create and store a new placement
            placement = self._place_subvertex(subvertex, self._graph,
                                              graph_to_subgraph_mapper)
            placements.add_placement(placement)

        return placements

    def _place_subvertex(self, subvertex, graph, graph_to_subgraph_mapper):
        #get resources of a subvertex
        vertex = graph_to_subgraph_mapper.get_vertex_from_subvertex(subvertex)
        resources = vertex.get_resources_used_by_atoms(
            subvertex.lo_atom, subvertex.hi_atom,
            graph.incoming_edges_to_vertex(vertex))

        # Record when a constraint is met at least somewhere to produce a richer
        # error message.
        chip_constraints_met = False
        core_constraints_met = False
        free_cores_met = False
        free_sdram_met = False
        cpu_speed_met = False
        dtcm_per_proc_met = False





        for chip in self.chips:
            x = None
            y = None
            p = None

            if constraints is not None:
                x = constraints.x
                y = constraints.y
                p = constraints.p

            if (((x is None) or (x == chip.x))
                    and ((y is None) or (y == chip.y))):
                chip_constraints_met |= True

                if ((p is None) or (chip.core_available[p] == True)):
                    core_constraints_met |= True
                    free_cores_met       |= (chip.free_cores > 0)
                    free_sdram_met       |= (chip.free_sdram >= resources.sdram)
                    cpu_speed_met        |= (chip.cpu_speed >= resources.clock_ticks)
                    dtcm_per_proc_met    |= (chip.dtcm_per_proc >= resources.dtcm)

                    if ((chip.free_cores > 0)
                            and (chip.free_sdram >= resources.sdram)
                            and (chip.cpu_speed >= resources.clock_ticks)
                            and (chip.dtcm_per_proc >= resources.dtcm)):
                        placement_chip = chip
                        break

        if placement_chip == None:
            msg = "Failed to place subvertex %s."%repr(subvertex)
            if not chip_constraints_met:
                msg += " Placement constraint to use chip (%s, %s) unmet."%(x,y)
            elif not core_constraints_met:
                msg += " Placement constraint to use core (%s, %s, %s) unmet."%(x,y,p)
            elif not free_cores_met:
                msg += " No free cores available on any chip."
            elif not (free_sdram_met and cpu_speed_met and dtcm_per_proc_met):
                msg += " No core available with:"
                if not free_sdram_met:
                    msg += " %s SDRAM;"%resources.sdram
                if not cpu_speed_met:
                    msg += " %s clock ticks;"%resources.clock_ticks
                if not dtcm_per_proc_met:
                    msg += " %s DTCM;"%resources.dtcm
                msg = msg.rstrip(";") + "."

            raise Exception(msg)

        core = placement_chip.assign_core(resources.sdram, p)
        return (placement_chip.x, placement_chip.y, core)




