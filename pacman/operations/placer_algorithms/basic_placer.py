
# pacman imports
from pacman.utilities.algorithm_utilities import placer_algorithm_utilities
from pacman.model.placements.placements import Placements
from pacman.model.placements.placement import Placement
from spinn_machine.utilities.progress_bar import ProgressBar
from pacman.utilities.utility_objs.resource_tracker import ResourceTracker

# general imports
import logging
logger = logging.getLogger(__name__)


class BasicPlacer(object):
    """ A basic placement algorithm that can place a partitioned_graph onto\
        a machine using the chips as they appear in the machine
    """

    def __call__(self, partitioned_graph, machine):
        """ Place a partitioned_graph so that each subvertex is placed on a\
                    core

        :param partitioned_graph: The partitioned_graph to place
        :type partitioned_graph:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_graph.PartitionedGraph`
        :return: A set of placements
        :rtype: :py:class:`pacman.model.placements.placements.Placements`
        :raise pacman.exceptions.PacmanPlaceException: If something\
                   goes wrong with the placement
        """

        # check that the algorithm can handle the constraints
        ResourceTracker.check_constraints(partitioned_graph.vertices)

        placements = Placements()
        ordered_subverts = \
            placer_algorithm_utilities.sort_vertices_by_known_constraints(
                partitioned_graph.vertices)

        # Iterate over subvertices and generate placements
        progress_bar = ProgressBar(len(ordered_subverts),
                                   "Placing graph vertices")
        resource_tracker = ResourceTracker(machine)
        for subvertex in ordered_subverts:

            # Create and store a new placement anywhere on the board
            (x, y, p, _, _) = resource_tracker.allocate_constrained_resources(
                subvertex.resources_required, subvertex.constraints)
            placement = Placement(subvertex, x, y, p)
            placements.add_placement(placement)
            progress_bar.update()
        progress_bar.end()
        return placements
