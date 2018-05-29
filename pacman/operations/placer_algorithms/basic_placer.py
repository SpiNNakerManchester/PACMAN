from spinn_utilities.progress_bar import ProgressBar

# pacman imports
from pacman.utilities.algorithm_utilities.placer_algorithm_utilities \
    import sort_vertices_by_known_constraints
from pacman.model.placements import Placement, Placements
from pacman.utilities.utility_objs import ResourceTracker

# general imports
import logging
logger = logging.getLogger(__name__)


class BasicPlacer(object):
    """ A basic placement algorithm that can place a machine graph onto\
        a machine using the chips as they appear in the machine
    """

    __slots__ = []

    def __call__(self, machine_graph, machine, plan_n_timesteps):
        """ Place a machine_graph so that each vertex is placed on a core

        :param machine_graph: The machine_graph to place
        :type machine_graph:\
            :py:class:`pacman.model.graphs.machine.MachineGraph`
        :param machine:\
            The machine with respect to which to partition the application\
            graph
        :type machine: :py:class:`spinn_machine.Machine`
        :param plan_n_timesteps: number of timesteps to plan for
        :type  plan_n_timesteps: int
        :return: A set of placements
        :rtype: :py:class:`pacman.model.placements.Placements`
        :raise pacman.exceptions.PacmanPlaceException: \
            If something goes wrong with the placement
        """

        # check that the algorithm can handle the constraints
        ResourceTracker.check_constraints(machine_graph.vertices)

        placements = Placements()
        vertices = sort_vertices_by_known_constraints(machine_graph.vertices)

        # Iterate over vertices and generate placements
        progress = ProgressBar(vertices, "Placing graph vertices")
        resource_tracker = ResourceTracker(machine, plan_n_timesteps)
        for vertex in progress.over(vertices):
            # Create and store a new placement anywhere on the board
            (x, y, p, _, _) = resource_tracker.allocate_constrained_resources(
                vertex.resources_required, vertex.constraints, None)
            placement = Placement(vertex, x, y, p)
            placements.add_placement(placement)
        return placements
