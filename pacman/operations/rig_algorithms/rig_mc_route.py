from six import iteritems
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities.rig_converters import (
    convert_from_rig_routes, convert_to_rig_graph, convert_to_vertex_to_p_dict,
    convert_to_vertex_xy_dict, create_rig_graph_constraints)
from pacman.minirig.place_and_route.route.ner import route


class RigMCRoute(object):
    """ Performs routing using rig algorithm
    """

    __slots__ = []

    def __call__(self, machine_graph, machine, placements):
        """

        :param machine_graph:
        :param machine:
        :param placements:  pacman.model.placements.placements.py
        :return:
        """
        progress_bar = ProgressBar(5, "Routing")

        vertex_to_xy_dict = convert_to_vertex_xy_dict(placements, machine)
        net_to_partition_dict = convert_to_rig_graph(machine_graph, vertex_to_xy_dict)
        progress_bar.update()

        rig_constraints = create_rig_graph_constraints(machine_graph, machine)
        progress_bar.update()

        vertex_to_p_dict = convert_to_vertex_to_p_dict(placements)
        progress_bar.update()
        partition_to_routingtree_dic = route(
            net_to_partition_dict, machine, rig_constraints, vertex_to_xy_dict, vertex_to_p_dict)
        progress_bar.update()

        routes = convert_from_rig_routes(partition_to_routingtree_dic)
        progress_bar.update()
        progress_bar.end()

        return routes
