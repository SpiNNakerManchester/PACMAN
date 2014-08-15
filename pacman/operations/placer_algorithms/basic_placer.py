from pacman.model.constraints.abstract_placer_constraint import \
    AbstractPlacerConstraint
from pacman.operations.placer_algorithms.abstract_placer_algorithm import\
    AbstractPlacerAlgorithm
from pacman.model.constraints.placer_chip_and_core_constraint \
    import PlacerChipAndCoreConstraint
from pacman.model.constraints.placer_subvertex_same_chip_constraint \
    import PlacerSubvertexSameChipConstraint
from pacman.model.placements.placements import Placements
from pacman.model.placements.placement import Placement
from pacman import exceptions
from pacman.utilities import utility_calls
from pacman.utilities.progress_bar import ProgressBar

import logging
from spinn_machine.sdram import SDRAM

logger = logging.getLogger(__name__)


class BasicPlacer(AbstractPlacerAlgorithm):
    """ An basic algorithm that can place a partitioned_graph onto a machine
    based off a raster behaviour
    """

    def __init__(self, machine, graph):
        """constructor to build a \
        pacman.operations.placer_algorithms.BasicPlacer.BasicPlacer
        :param machine: The machine on which to place the partitionable_graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        """
        AbstractPlacerAlgorithm.__init__(self, machine, graph)
        self._supported_constraints.append(PlacerChipAndCoreConstraint)
        self._supported_constraints.append(PlacerSubvertexSameChipConstraint)

    def place(self, subgraph, graph_mapper):
        """ Place a partitioned_graph so that each subvertex is placed on a core

        :param subgraph: The partitioned_graph to place
        :type subgraph:
        :py:class:`pacman.model.partitioned_graph.partitioned_graph.PartitionedGraph`
        :param graph_mapper: the mappings between partitionable_graph and partitioned_graph
        :type graph_mapper:
    pacman.model.graph_mapper.graph_mapper.GraphMapper
        :return: A set of placements
        :rtype: :py:class:`pacman.model.placements.placements.Placements`
        :raise pacman.exceptions.PacmanPlaceException: If something\
                   goes wrong with the placement
        """
        #check that the algorithm can handle the constraints
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=subgraph.subvertices,
            supported_constraints=self._supported_constraints,
            abstract_constraint_type=AbstractPlacerConstraint)

        placements = Placements()
        ordered_subverts = \
            utility_calls.sort_objects_by_constraint_authority(
                subgraph.subvertices)

        # Iterate over subvertices and generate placements
        progress_bar = ProgressBar(len(ordered_subverts),
                                   "for placing the partitioned_graphs "
                                   "subvertices")
        for subvertex in ordered_subverts:

            # Create and store a new placement
            placement = self._place_subvertex(subvertex, self._graph,
                                              graph_mapper,
                                              placements)
            placements.add_placement(placement)
            progress_bar.update()
        progress_bar.end()
        return placements

    def _place_subvertex(self, subvertex, graph, graph_to_subgraph_mapper,
                         placements):
        """ place a subvertex on some processor to be determined. \
        SHOULD NOT BE CALLED OUTSIDE THIS CLASS

        :param subvertex: the subvertex to be placed
        :param graph: the partitionable_graph obejct of the application
        :param graph_to_subgraph_mapper: the partitionable_graph to partitioned_graph mapper
        :param placements: the current placements
        :type subvertex: pacman.models.partitioned_graph.subvertex.PartitionedVertex
        :type graph: pacman.models.partitionable_graph.partitionable_graph.Graph
        :type graph_to_subgraph_mapper: pacamn.models.graph_mapper.graphSubgraphMapper
        :type placements: pacman.model.placements.placements.Placements
        :return: placement object for this subvertex
        :rtype: pacman.model.placements.placement.Placement
        :raise PacmanPlaceException: when either a core has already been \
        assigned the subvertex's required core or there are no more cores \
        avilable to be assigned or theres not enough memory of the avilable \
        cores to assign this subvertex.
        """

        #get resources of a subvertex
        vertex = graph_to_subgraph_mapper.get_vertex_from_subvertex(subvertex)
        resources = vertex.get_resources_used_by_atoms(
            subvertex.lo_atom, subvertex.hi_atom,
            graph.incoming_edges_to_vertex(vertex))

        placement_constraints = \
            utility_calls.locate_constraints_of_type(subvertex.constraints,
                                                     AbstractPlacerConstraint)
        x, y, p = self._try_to_place(placement_constraints, resources,
                                     subvertex.label, placements)
        return Placement(x=x, y=y, p=p, subvertex=subvertex)

    def _try_to_place(self, placement_constraints, resources, subvert_label,
                      placements):
        """helper method for partitioners
        :param placement_constraints: the placement constraints of a vertex
        :param resources: the sdram, cpu and dctm usage of the subvertex
        :param subvert_label: the label of the subvert
        :param placements: the placement container
        :type placements: pacman.model.placements.placements.Placements
        :type resources: pacman.model.resources.resource_container.ResourceContainer
        :type placement_constraints: iterable of implementations of
        pacaman.model.constraints.abstractPlacementConstraint
        :type subvert_label: str
        :return: the x,y,p coord of the placement
        :rtype: int, int, int
        :raise None: this method does not raise any known exceptions
        """
        placement_constraint = \
            self._reduce_constraints(placement_constraints, subvert_label,
                                     placements)

        #if there's a placement constraint, then check out the chip and only
        # that chip
        if placement_constraint is not None:
            return self._deal_with_constraint_placement(placement_constraint,
                                                        subvert_label,
                                                        resources)
        else:
            chips = self._machine.chips
            return self._deal_with_non_constrained_placement(subvert_label,
                                                              resources,
                                                              chips)

    def _deal_with_constraint_placement(self, placement_constraint,
                                        subvertex_label,
                                        subvertex_resources):
        """ place a subvertex on some processor to be determined. \
        SHOULD NOT BE CALLED OUTSIDE THIS CLASS

        :param subvertex_label: the label of the subvertex to be placed
        :param placement_constraint: the placement constraint of this subvertex
        :param subvertex_resources: the resource required by this subvertex
        :type subvertex_label: str
        :type placement_constraint: pacman.constraints.placer_chip_and_core_constraint
        :type subvertex_resources: pacman.model.resoruces.resourceContainer.ResourceContainer
        :return: placement object for this subvertex
        :rtype: pacman.model.placements.placement.Placement
        :raise PacmanPlaceException: when either a core has already been \
        assigned the subvertex's required core or there are no more cores \
        available to be assigned or theres not enough memory of the available \
        cores to assign this subvertex.
        """
        x = placement_constraint.x
        y = placement_constraint.y
        p = placement_constraint.p
        if not self._placement_tracker.has_available_cores_left(x, y, p):
            if p is None:
                raise exceptions.PacmanPlaceException(
                    "cannot place subvertex {} in chip {}:{} as there is no"
                    "available cores to place subvertices on"
                    .format(subvertex_label, x, y))
            else:
                raise exceptions.PacmanPlaceException(
                    "cannot place subvertex {} in processor {}:{}:{} as "
                    "it has already been assigned".format(subvertex_label,
                                                          x, y))
        else:
            chip_usage = self._sdram_tracker.get_usage(x, y)
            total_usage_after_assigment =\
                chip_usage + subvertex_resources.sdram.get_value()
            if total_usage_after_assigment <= SDRAM.DEFAULT_SDRAM_BYTES:
                x, y, p = self._placement_tracker.assign_core(x, y, p)
                self._sdram_tracker.add_usage(
                    x, y, subvertex_resources.sdram.get_value())
                return x, y, p
            else:
                raise exceptions.PacmanPlaceException(
                    "cannot place subvertex {} on chip {}:{} as there is "
                    "not enough available memory".format(subvertex_label, x, y))

    def _deal_with_non_constrained_placement(self, subvertex_label,
                                              used_resources,
                                              chips_in_a_ordering):
        """ place a subvertex which doesnt have a constraint

        :param subvertex_label: the of the subvert to place
        :param used_resources: the used_resources used by this subvertex
        :param chips_in_a_ordering: the chips available from the machine in \
         some predetermined ordering.
        :type subvertex_label: str
        :used_resourcesurces: pacman.model.resources.resource_container.ResourceContainer
        :type chips_in_a_ordering: iterable of spinnMachine.chip,Chip
        :return a placement object for this subvertex
        :rtype: pacman.model.placements.placement.Placement
        :raise PacmanPlaceException: when it is not possible to place the \
        subvertex for either: 1. not enough sdram, 2. no more available cores,
         3. not enough cpu or 4. not enough clock cycles available
        """
        # Record when a constraint is met at least somewhere to produce a richer
        # error message.
        free_cores_met = False
        free_sdram_met = False
        cpu_speed_met = False
        dtcm_per_proc_met = False
        for chip in chips_in_a_ordering:
            for processor in chip.processors:
                if (processor.processor_id != 0 and
                        self._placement_tracker.has_available_cores_left(
                        chip.x, chip.y, processor.processor_id)):
                    #locate available SDRAM
                    available_sdram = \
                        chip.sdram.size - \
                        (self._sdram_tracker.get_usage(chip.x, chip.y))
                    free_cores_met = True
                    free_sdram_met |= \
                        available_sdram >= used_resources.sdram.get_value()
                    cpu_speed_met |= (processor.clock_speed >=
                                      used_resources.cpu.get_value())
                    dtcm_per_proc_met |= (processor.dtcm_available >=
                                          used_resources.dtcm.get_value())

                    if (available_sdram >= used_resources.sdram.get_value()
                        and (processor.cpu_cycles_available >=
                             used_resources.cpu.get_value())
                        and (processor.dtcm_available >=
                             used_resources.dtcm.get_value())):
                        x, y, p = self._placement_tracker.assign_core(
                            chip.x, chip.y, processor.processor_id)
                        self._sdram_tracker.add_usage(
                            x, y, used_resources.sdram.get_value())
                        return x, y, p

        msg = "Failed to place subvertex {}.".format(subvertex_label)
        if not free_cores_met:
            msg += " No free cores available on any chip."
        elif not (free_sdram_met and cpu_speed_met and dtcm_per_proc_met):
            msg += " No core available with:"
            if not free_sdram_met:
                msg += " {} SDRAM;".format(used_resources.sdram.get_value())
            if not cpu_speed_met:
                msg += " {} clock ticks;".format(used_resources.cpu.get_value())
            if not dtcm_per_proc_met:
                msg += " {} DTCM;".format(used_resources.dtcm.get_value())
            msg = msg.rstrip(";") + "."
        raise exceptions.PacmanPlaceException(msg)
