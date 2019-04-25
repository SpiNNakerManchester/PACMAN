from six import iteritems
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities.rig_converters import (
    convert_from_rig_routes, convert_to_rig_graph, convert_to_rig_machine,
    convert_to_vertex_xy_dict, convert_to_vertex_to_p_dict, create_rig_graph_constraints,
    create_rig_machine_constraints)
from pacman.minirig.place_and_route.route.ner import route


class RigRoute(object):
    """ Performs routing using rig algorithm
    """

    __slots__ = []

    def __call__(self, machine_graph, machine, placements):
        progress_bar = ProgressBar(7, "Routing")

        vertices_resources, nets, net_names = convert_to_rig_graph(
            machine_graph)
        progress_bar.update()

        rig_machine = convert_to_rig_machine(machine)
        progress_bar.update()

        rig_constraints = create_rig_machine_constraints(machine)
        progress_bar.update()

        rig_constraints.extend(create_rig_graph_constraints(
            machine_graph, machine))
        progress_bar.update()

        vertex_to_xy_dict = convert_to_vertex_xy_dict(placements, machine)
        vertex_to_p_dict = convert_to_vertex_to_p_dict(placements)
        progress_bar.update()

        rig_routes = route(
            vertices_resources, nets, rig_machine, rig_constraints,
            vertex_to_xy_dict, vertex_to_p_dict)
        rig_routes = {
            name: rig_routes[net] for net, name in iteritems(net_names)}
        progress_bar.update()

        routes = convert_from_rig_routes(rig_routes)
        progress_bar.update()
        progress_bar.end()

        return routes
